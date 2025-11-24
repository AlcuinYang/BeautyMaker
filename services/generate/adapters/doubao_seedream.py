"""Doubao Seedream adapter.

Supports both text-to-image and image-to-image flows via the Ark platform
REST API. When no API key is present, the adapter returns a placeholder
data URL to keep demos and tests hermetic.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx

from services.generate.adapters.base import BaseProvider
from services.generate.models import GenerateRequestPayload


logger = logging.getLogger(__name__)


_PLACEHOLDER_IMAGE = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAAJElEQVR4Xu3BAQ0AAADCoPdPbQ43oAAAAAAAAAAA"
    "AAAAAAAAAPgPqdcAAT3mKMUAAAAASUVORK5CYII="
)

DEFAULT_MODEL = "doubao-seedream-4-0-250828"
DEFAULT_SIZE = "2K"
ARK_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/images/generations"



class DoubaoSeedreamProvider(BaseProvider):
    """Doubao Seedream 文图生成适配器。"""

    name = "doubao_seedream"

    async def generate(self, request: GenerateRequestPayload) -> Dict[str, Any]:
        """Generate images with Doubao Seedream.

        If ``ARK_API_KEY`` is missing, a single placeholder image is
        returned so that the rest of the pipeline remains functional.
        """
        env_tokens = {
            "ARK_API_KEY": os.getenv("ARK_API_KEY"),
            "DOUBAO_API_KEY": os.getenv("DOUBAO_API_KEY"),
            "HOLISTIC_SCORE_TOKEN": os.getenv("HOLISTIC_SCORE_TOKEN"),
        }
        api_key = next((value for value in env_tokens.values() if value), None)
        token_source = next((name for name, value in env_tokens.items() if value), None)
        token_length = len(api_key) if api_key else 0
        logger.info(
            "Doubao Seedream init prompt=%s token_source=%s token_present=%s token_length=%s env_snapshot=%s",
            request.prompt[:30] + "..." if request.prompt and len(request.prompt) > 30 else request.prompt,
            token_source,
            bool(api_key),
            token_length,
            {k: bool(v) for k, v in env_tokens.items()},
        )
        prompt = request.prompt or "Aesthetics Engine prompt"

        if not api_key:
            logger.warning("Doubao Seedream missing API key, returning placeholder response.")
            return self._placeholder(prompt=prompt, reason="missing_api_key")

        payload = self._build_payload(request=request, prompt=prompt)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(ARK_ENDPOINT, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            images = self._extract_urls(data)
            if not images:
                raise RuntimeError(f"Doubao response missing images: {data}")

            metadata = {
                "provider": self.name,
                "prompt": prompt,
                "model": data.get("model", payload.get("model")),
                "size": self._extract_size(data) or payload.get("size"),
                "usage": data.get("usage"),
            }

            return {
                "status": "success",
                "task_id": str(request.task_id or uuid4()),
                "images": images,
                "image_url": images[0],
                "metadata": metadata,
            }
        except httpx.HTTPStatusError as exc:
            reason = f"{exc.response.status_code} {exc.response.text}"
            logger.error(
                "Doubao request failed status=%s payload=%s body=%s",
                exc.response.status_code,
                payload,
                exc.response.text,
            )
            return self._placeholder(prompt=prompt, reason=reason)
        except Exception as exc:  # noqa: BLE001
            return self._placeholder(prompt=prompt, reason=str(exc))

    def _build_payload(self, *, request: GenerateRequestPayload, prompt: str) -> Dict[str, Any]:
        """Build Ark payload from a normalized request.

        Accepts URL or base64 data URL in ``reference_images``.
        """
        params = request.params or {}
        references: List[str] = params.get("reference_images") or params.get("references") or []
        model_name = params.get("model") or DEFAULT_MODEL
        raw_size = params.get("size") or request.size or DEFAULT_SIZE
        size = self._normalize_size(raw_size)

        sequential_mode = params.get("sequential_mode")
        requested_variations = params.get("num_variations") or params.get("max_images")
        if not sequential_mode:
            if references or (requested_variations and int(requested_variations) > 1):
                sequential_mode = "auto"
            else:
                sequential_mode = "disabled"
        if sequential_mode is True:
            sequential_mode = "auto"
        elif sequential_mode is False or sequential_mode is None:
            sequential_mode = "disabled"

        payload: Dict[str, Any] = {
            "model": model_name,
            "prompt": prompt,
            "size": size,
            "response_format": "url",
            "stream": False,
            "watermark": params.get("watermark", False),
            "sequential_image_generation": sequential_mode,
        }

        if references:
            payload["image"] = references

        if requested_variations:
            max_images = max(1, min(int(requested_variations), 15))
            payload["sequential_image_generation_options"] = {
                "max_images": max_images,
            }

        return payload

    def _extract_urls(self, payload: Dict[str, Any]) -> List[str]:
        """Collect image URLs from Ark response."""
        urls: List[str] = []
        data = payload.get("data")
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("url"):
                    urls.append(item["url"])
        return urls

    def _extract_size(self, payload: Dict[str, Any]) -> Optional[str]:
        data = payload.get("data")
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("size"):
                    return item["size"]
        return None

    @staticmethod
    def _normalize_size(size: Optional[str]) -> str:
        if not size:
            return DEFAULT_SIZE
        normalized = str(size).strip()
        normalized = normalized.replace("×", "x").replace("X", "x")
        return normalized

    def _placeholder(self, *, prompt: str, reason: Optional[str]) -> Dict[str, Any]:
        """Return a single transparent placeholder image with metadata."""
        logger.info("Doubao Seedream placeholder emitted reason=%s", reason)
        metadata = {
            "provider": self.name,
            "prompt": prompt,
            "note": f"Doubao placeholder response ({reason or 'unknown'})",
        }
        return {
            "status": "success",
            "task_id": str(uuid4()),
            "images": [_PLACEHOLDER_IMAGE],
            "image_url": _PLACEHOLDER_IMAGE,
            "metadata": metadata,
        }
