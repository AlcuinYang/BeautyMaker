from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import httpx

logger = logging.getLogger(__name__)

try:  # Optional dependency
    import numpy as _np
except ImportError:  # pragma: no cover
    _np = None


def _resolve_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return Path(__file__).resolve().parent / path


def _to_vector(values: Sequence[float]) -> Optional[Any]:
    if _np is None:
        return None
    try:
        vector = _np.asarray(list(values), dtype=_np.float32)
        norm = _np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector
    except Exception:  # pragma: no cover
        return None


class PromptBankCN:
    """基于 Qwen 百炼向量服务的中文 Prompt Bank 检索模块。"""

    def __init__(
        self,
        path: str = "prompt_bank_cn.json",
        *,
        alpha: float = 0.7,
    ) -> None:
        self.path = _resolve_path(path)
        self.alpha = max(0.0, min(1.0, alpha))
        self.bank = self._load_prompts(self.path)
        self._id_index = {item.get("id"): item for item in self.bank}
        self._embedding_cache: Dict[str, Optional[Any]] = {}

    @staticmethod
    def _load_prompts(path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            raise FileNotFoundError(f"Prompt bank 文件不存在: {path}")
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, list):
            raise ValueError("Prompt bank 数据格式错误，应为列表。")
        return data

    def retrieve(
        self,
        image_emb: Optional[Sequence[float]],
        platform: str,
        *,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        platform = platform or ""
        query_vec = _to_vector(image_emb) if image_emb is not None else None
        if query_vec is None and description:
            query_vec = self.embed_text(description)

        template_scores: List[tuple[float, Dict[str, Any]]] = []
        for template in self.bank:
            weight = float(template.get("权重") or 0.5)
            template_vec = self._ensure_template_vector(template)
            similarity = 0.0
            if query_vec is not None and template_vec is not None and _np is not None:
                similarity = float(_np.dot(query_vec, template_vec))
                similarity = max(-1.0, min(1.0, similarity))
            else:
                similarity = self._tag_overlap_similarity(template, platform)

            combined = self.alpha * similarity + (1 - self.alpha) * weight + self._platform_bonus(template, platform)
            template_scores.append((combined, template))

        if not template_scores:
            raise RuntimeError("Prompt bank 为空，无法检索模板。")

        template_scores.sort(key=lambda item: item[0], reverse=True)
        best_score, best_template = template_scores[0]
        logger.debug(
            "PromptBankCN 选中模板 %s (score=%.4f weight=%.3f)",
            best_template.get("id"),
            best_score,
            best_template.get("权重"),
        )
        return best_template

    def fuse(self, template: Dict[str, Any], desc: Dict[str, Any]) -> str:
        raw_template = template.get("提示模板") or ""
        product = desc.get("product") or desc.get("category") or "产品"
        style = desc.get("style") or template.get("风格") or "质感商业风"
        style_keywords = desc.get("style_keywords") or desc.get("keywords")
        if isinstance(style_keywords, list) and style_keywords:
            keyword_str = "、".join([item for item in style_keywords if isinstance(item, str) and item])
            if keyword_str:
                style = keyword_str if not style else f"{style}、{keyword_str}"
        platform = desc.get("platform") or "电商平台"
        result = (
            raw_template.replace("{product}", product)
            .replace("{style}", style)
            .replace("{platform}", platform)
        )
        return result.strip()

    def embed_text(self, text: str) -> Optional[Any]:
        vector = self._fetch_embedding(text)
        if vector is not None and _np is not None:
            norm = _np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
        return vector

    def update_weight(self, template_id: str, score: float) -> None:
        template = self._id_index.get(template_id)
        if not template:
            logger.warning("尝试更新不存在的模板权重: %s", template_id)
            return
        template["权重"] = max(0.0, min(1.0, float(score)))

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        return self._id_index.get(template_id)

    def templates(self) -> Iterable[Dict[str, Any]]:
        return self.bank

    def _ensure_template_vector(self, template: Dict[str, Any]) -> Optional[Any]:
        if _np is None:
            return None
        cached = template.get("_vector")
        if cached is not None:
            return cached

        stored = template.get("embedding")
        vector = None
        if isinstance(stored, list) and stored:
            vector = _to_vector(stored)

        if vector is None:
            text_parts = [
                template.get("提示模板") or "",
                template.get("风格") or "",
                ",".join(template.get("美学标签") or []),
            ]
            text = " ".join(part for part in text_parts if part).strip()
            vector = self._fetch_embedding(text)

        if vector is not None and _np is not None:
            template["_vector"] = vector
        return vector

    def _fetch_embedding(self, text: str) -> Optional[Any]:
        text = (text or "").strip()
        if not text:
            return None
        cached = self._embedding_cache.get(text)
        if cached is not None:
            return cached

        api_key = _get_qwen_api_key()
        if not api_key:
            logger.warning("DashScope/Qwen API key 未配置，PromptBank 将退化为标签匹配。")
            self._embedding_cache[text] = None
            return None

        try:
            vector = _request_qwen_embedding(text=text, api_key=api_key)
            if vector is not None and _np is not None:
                vector = _np.asarray(vector, dtype=_np.float32)
                norm = _np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm
            self._embedding_cache[text] = vector
            return vector
        except Exception as exc:  # pragma: no cover
            logger.warning("调用 Qwen embedding 失败 [%s]: %s", text[:24], exc)
            self._embedding_cache[text] = None
            return None

    @staticmethod
    def _platform_bonus(template: Dict[str, Any], platform: str) -> float:
        platforms = template.get("适用平台") or []
        if not platform or not isinstance(platforms, list):
            return 0.0
        normalized = platform.strip()
        if normalized in platforms:
            return 0.05
        return 0.0

    @staticmethod
    def _tag_overlap_similarity(template: Dict[str, Any], platform: str) -> float:
        tags = template.get("美学标签") or []
        if not tags:
            return 0.0
        platform = platform or ""
        matches = sum(1 for tag in tags if tag and tag in platform)
        return matches / max(len(tags), 1)


@lru_cache(maxsize=1)
def _get_qwen_api_key() -> Optional[str]:
    for key in ("DASHSCOPE_API_KEY", "QWEN_API_KEY", "ALIYUN_API_KEY"):
        value = os.getenv(key)
        if value:
            return value
    return None


def _request_qwen_embedding(*, text: str, api_key: str) -> Optional[List[float]]:
    endpoint = os.getenv(
        "QWEN_EMBEDDING_ENDPOINT",
        "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding",
    )
    model = os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v1")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload_candidates = [
        {"model": model, "input": {"texts": [text]}},
        {"model": model, "input": [{"text": text}]},
        {"model": model, "input": {"text": text}},
    ]

    last_error: Optional[Exception] = None
    for payload in payload_candidates:
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()
            embeddings = (
                body.get("output", {}).get("embeddings")
                or body.get("data")
                or body.get("embeddings")
            )
            if not embeddings:
                logger.warning("Qwen embedding response缺少向量: %s", body)
                return None
            embedding = embeddings[0].get("embedding") if isinstance(embeddings[0], dict) else None
            if embedding is None and isinstance(embeddings[0], list):
                embedding = embeddings[0]
            if isinstance(embedding, list):
                return [float(x) for x in embedding]
            logger.warning("无法解析 Qwen embedding 响应: %s", body)
            return None
        except httpx.HTTPStatusError as exc:
            last_error = exc
            logger.warning(
                "调用 Qwen embedding 失败，payload=%s status=%s body=%s",
                payload,
                exc.response.status_code,
                exc.response.text,
            )
        except Exception as exc:  # pragma: no cover
            last_error = exc
            logger.warning("调用 Qwen embedding 异常: %s", exc)

    if last_error:
        raise last_error
    return None
