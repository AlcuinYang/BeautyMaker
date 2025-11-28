"""Tongyi Qianwen (Qwen-Image) adapter.

Qwen-Image is a synchronous multimodal generation API that supports
complex text rendering, multi-line layouts, and detailed image generation.
Ideal for posters, cartoons, and text-heavy images.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Dict

import httpx

from services.generate.adapters.base import BaseProvider
from services.generate.models import GenerateRequestPayload

logger = logging.getLogger(__name__)


class QwenProvider(BaseProvider):
    """Tongyi Qianwen (Qwen-Image) synchronous generation adapter."""

    name = "qwen"
    model_name = "qwen-image-plus"

    # Qwen-Image uses synchronous API
    endpoint = (
        "https://dashscope.aliyuncs.com/api/v1/services/aigc"
        "/multimodal-generation/generation"
    )
    timeout_seconds = 120.0

    async def generate(self, request: GenerateRequestPayload) -> Dict[str, Any]:
        """Generate images using Qwen-Image synchronous API.

        Note: Qwen-Image is text-only (no reference images support).
        """
        api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Missing DASHSCOPE_API_KEY for Qwen-Image integration."
            )

        prompt = request.prompt
        if not prompt:
            raise ValueError("Prompt is required for Qwen-Image provider.")

        # Qwen-Image doesn't support reference images
        reference_images = request.params.get("reference_images") or []
        if reference_images:
            logger.warning(
                "Qwen-Image does not support reference images. "
                "Use 'wan' provider for i2i tasks."
            )

        # Parse parameters (force into Qwen-Image supported sizes)
        size = self._resolve_size(request.size or "1328*1328")
        negative_prompt = request.params.get("negative_prompt", "")
        prompt_extend = request.params.get("prompt_extend", False)
        watermark = request.params.get("watermark", False)
        seed = request.params.get("seed")

        # Build request payload (Qwen-Image uses messages format)
        payload: Dict[str, Any] = {
            "model": request.params.get("model") or self.model_name,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}],
                    }
                ]
            },
            "parameters": {
                "size": size,
                "negative_prompt": negative_prompt,
                "prompt_extend": prompt_extend,
                "watermark": watermark,
            },
        }

        # Add seed if provided
        if seed is not None:
            payload["parameters"]["seed"] = int(seed)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        logger.info(
            "Calling Qwen-Image API model=%s size=%s prompt_extend=%s",
            payload["model"],
            size,
            prompt_extend,
        )

        timeout = httpx.Timeout(self.timeout_seconds)

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(
                    self.endpoint, json=payload, headers=headers
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                details = exc.response.text if exc.response is not None else str(exc)
                raise RuntimeError(
                    f"Qwen-Image request failed: {details}"
                ) from exc

            body = response.json()

            error_code = body.get("code")
            if error_code:
                message = body.get("message") or body
                raise RuntimeError(
                    f"Qwen-Image request failed: {message} (code={error_code})"
                )

            # Extract image URL from response
            images = self._extract_images(body)
            if not images:
                raise RuntimeError(
                    f"No images returned from Qwen-Image: {body}"
                )

            metadata = {
                "provider": self.name,
                "model": payload["model"],
                "size": size,
                "mode": "text2image",
                "usage": body.get("usage"),
                "request_id": body.get("request_id"),
            }

            return {
                "status": "success",
                "task_id": str(request.task_id or uuid.uuid4()),
                "images": images,
                "image_url": images[0] if images else "",
                "metadata": metadata,
            }

    def _extract_images(self, body: Dict[str, Any]) -> list[str]:
        """Extract image URLs from Qwen-Image response."""
        try:
            output = body.get("output", {})
            choices = output.get("choices", [])

            images = []
            for choice in choices:
                message = choice.get("message", {})
                content = message.get("content", [])

                for item in content:
                    if isinstance(item, dict) and "image" in item:
                        images.append(item["image"])

            return images
        except Exception as exc:
            logger.warning("Failed to extract images from response: %s", exc)
            return []

    def _resolve_size(self, size: str) -> str:
        """Resolve size to Qwen-Image supported format (W*H).

        Qwen-Image only accepts these sizes:
        - 1664*928 (16:9)
        - 1472*1140 (4:3)
        - 1328*1328 (1:1, default)
        - 1140*1472 (3:4)
        - 928*1664 (9:16)
        Any other input will be mapped到最接近的合法尺寸，防止 API 返回 InvalidParameter。
        """
        allowed_sizes = {
            "1664*928",
            "1472*1140",
            "1328*1328",
            "1140*1472",
            "928*1664",
        }

        # Normalize separators
        raw = (size or "").strip()
        normalized = raw.replace("×", "x").replace("X", "x")
        size_lower = normalized.lower().replace("x", "*")

        # Direct hit
        if size_lower in allowed_sizes:
            return size_lower

        # Common aspect ratios
        ratio_map = {
            "16:9": "1664*928",
            "4:3": "1472*1140",
            "1:1": "1328*1328",
            "3:4": "1140*1472",
            "9:16": "928*1664",
        }
        if normalized in ratio_map:
            return ratio_map[normalized]

        # Parse WxH / W*H and map to nearest allowed size
        if "*" in size_lower:
            try:
                width_str, height_str = size_lower.split("*", 1)
                width = int(width_str.strip())
                height = int(height_str.strip())
                if height == 0:
                    return "1328*1328"
                ratio = width / height
                if ratio >= 1.5:  # 16:9 or wider
                    return "1664*928"
                if ratio >= 1.2:  # 4:3
                    return "1472*1140"
                if ratio >= 0.9:  # 1:1
                    return "1328*1328"
                if ratio >= 0.6:  # 3:4
                    return "1140*1472"
                return "928*1664"  # 9:16 or taller
            except (ValueError, IndexError):
                logger.debug("Qwen size parse failed for '%s', using default", size)

        # Default safest size
        return "1328*1328"
