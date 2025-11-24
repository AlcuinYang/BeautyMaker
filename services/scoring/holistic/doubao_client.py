from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from services.common.models import GeneratedImage

logger = logging.getLogger(__name__)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PROMPT_PATH = PROJECT_ROOT / "prompts" / "doubao_aesthetic.prompt"
DEFAULT_MODEL_ID = "doubao-seed-1-6-vision-250815"
DEFAULT_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"


@dataclass(slots=True)
class DoubaoAestheticResult:
    scores: Dict[str, float]
    comments: Dict[str, str]


class DoubaoAestheticClient:
    """Client for querying Doubao vision model to obtain aesthetic scores."""

    def __init__(
        self,
        *,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
        system_prompt_path: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        # 按需求写死接口、模型与 Prompt 路径，可选参数仅作为后门备用
        self._api_url = DEFAULT_ENDPOINT
        self._model = DEFAULT_MODEL_ID
        prompt_path = DEFAULT_PROMPT_PATH
        self._system_prompt = self._load_prompt(str(prompt_path))
        env_tokens = {
            "ARK_API_KEY": os.getenv("ARK_API_KEY"),
            "DOUBAO_API_KEY": os.getenv("DOUBAO_API_KEY"),
            "HOLISTIC_SCORE_TOKEN": os.getenv("HOLISTIC_SCORE_TOKEN"),
        }
        selected_source = "init_param" if api_key else None
        resolved_key = api_key
        if not resolved_key:
            for name, value in env_tokens.items():
                if value:
                    resolved_key = value
                    selected_source = name
                    break

        self._api_key = resolved_key
        token_length = len(self._api_key) if self._api_key else 0
        logger.info(
            "Doubao aesthetic client init endpoint=%s model=%s prompt_loaded=%s token_source=%s token_present=%s token_length=%s",
            self._api_url,
            self._model,
            bool(self._system_prompt),
            selected_source,
            bool(self._api_key),
            token_length,
        )
        self._timeout = timeout
        self._enabled = bool(self._system_prompt and self._api_key and self._api_url and self._model)
        if not self._enabled:
            logger.warning(
                "Doubao aesthetic client disabled (missing prompt/model/url/api key)."
                " api_url=%s model=%s prompt=%s token=%s",
                self._api_url,
                self._model,
                bool(self._system_prompt),
                bool(self._api_key),
            )
            logger.warning("Doubao aesthetic env snapshot: %s", {k: bool(v) for k, v in env_tokens.items()})

    async def evaluate(self, image: GeneratedImage) -> Optional[DoubaoAestheticResult]:
        if not self._enabled:
            return None

        image_payload = self._prepare_image_content(image.url)
        if image_payload is None:
            logger.debug("Doubao aesthetic skipped: unable to prepare image payload for %s", image.url)
            return None

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": self._system_prompt},
                {
                    "role": "user",
                    "content": [
                        image_payload,
                        {"type": "text", "text": "请直接输出JSON结果"},
                    ],
                },
            ],
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._api_url, json=payload, headers=headers)
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Doubao aesthetic request failed: %s", exc)
            return None

        try:
            body = response.json()
        except json.JSONDecodeError as exc:  # noqa: PERF203
            logger.warning("Doubao aesthetic response is not JSON: %s", exc)
            return None

        parsed = self._extract_result(body)
        if not isinstance(parsed, dict):
            logger.debug("Doubao aesthetic response missing JSON content: %s", body)
            return None

        try:
            logger.info("Doubao aesthetic raw result: %s", json.dumps(parsed, ensure_ascii=False))
        except (TypeError, ValueError):
            logger.info("Doubao aesthetic raw result: %s", parsed)

        return self._map_scores(parsed)

    def _prepare_image_content(self, source: str) -> Optional[Dict[str, Any]]:
        if not source:
            return None
        if source.startswith("data:"):
            _, _, encoded = source.partition(",")
            if not encoded:
                return None
            return {
                "type": "image_url",
                "image_url": {
                    "url": source,
                },
            }
        return {
            "type": "image_url",
            "image_url": {
                "url": source,
            },
        }

    def _extract_result(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        candidates: list[str] = []

        output = payload.get("output")
        if isinstance(output, dict):
            text = output.get("text") or output.get("result") or output.get("content")
            if isinstance(text, str):
                candidates.append(text)

        choices = payload.get("choices")
        if isinstance(choices, list):
            for choice in choices:
                message = choice.get("message") if isinstance(choice, dict) else None
                if not isinstance(message, dict):
                    continue
                content = message.get("content")
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict):
                            text = part.get("text")
                            if isinstance(text, str):
                                candidates.append(text)
                elif isinstance(content, str):
                    candidates.append(content)

        data = payload.get("data")
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    text = item.get("text") or item.get("result") or item.get("content")
                    if isinstance(text, str):
                        candidates.append(text)
        elif isinstance(data, dict):
            text = data.get("text") or data.get("result") or data.get("content")
            if isinstance(text, str):
                candidates.append(text)

        for text in candidates:
            if not isinstance(text, str):
                continue
            text = text.strip()
            if not text:
                continue
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        return None

    def _map_scores(self, payload: Dict[str, Any]) -> Optional[DoubaoAestheticResult]:
        mapping = {
            "light_color": "color_score",
            "composition": "contrast_score",
            "clarity_integrity": "clarity_eval",
            "style_coherence": "noise_eval",
            "emotional_impact": "quality_score",
        }

        scores: Dict[str, float] = {}
        comments: Dict[str, str] = {}

        for source_key, target_key in mapping.items():
            entry = payload.get(source_key)
            if isinstance(entry, dict):
                value = self._normalize_score(entry.get("score"))
                if value is not None:
                    scores[target_key] = value
                comment = entry.get("comment")
                if isinstance(comment, str) and comment.strip():
                    comments[target_key] = comment.strip()
            else:
                value = self._normalize_score(entry)
                if value is not None:
                    scores[target_key] = value

        final_score = self._normalize_score(payload.get("final_score"))
        if final_score is not None:
            scores["holistic"] = final_score

        if not scores:
            return None

        return DoubaoAestheticResult(scores=scores, comments=comments)

    @staticmethod
    def _normalize_score(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        if numeric < 0:
            numeric = 0.0
        if numeric > 10:
            return 1.0
        return round(max(0.0, min(numeric / 10.0, 1.0)), 3)

    @staticmethod
    def _load_prompt(path: str) -> str:
        return _cached_prompt(path)


@lru_cache(maxsize=8)
def _cached_prompt(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError as exc:  # noqa: PERF203
        logger.warning("Failed to load Doubao aesthetic prompt: %s", exc)
        return ""
