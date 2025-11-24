"""Qwen (Tongyi Qianwen) image adapters.

Supports both text‑to‑image (t2i) and image‑to‑image (i2i) with DashScope.
This adapter builds payloads, submits async tasks and polls until results
are ready, returning a simple dict with image URLs for the pipeline.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
from io import BytesIO
from typing import Any, Dict, Optional, Sequence, Tuple
from uuid import uuid4

import httpx
from PIL import Image

from services.generate.adapters.base import BaseProvider
from services.generate.models import GenerateRequestPayload

logger = logging.getLogger(__name__)


class QwenProvider(BaseProvider):
    """Alibaba Cloud Tongyi Qianwen (Qwen) image generation adapter."""

    name = "qwen"
    max_reference_image_bytes = 4_500_000  # ≈6 MB when base64 encoded
    submit_endpoint = (
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
    )
    image_to_image_endpoint = (
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2image/image-synthesis"
    )
    task_endpoint = "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
    timeout_seconds = 30.0
    poll_interval = 2.0
    poll_timeout = 90.0

    async def generate(self, request: GenerateRequestPayload) -> Dict[str, Any]:
        """Generate images based on a normalized payload.

        Decides t2i vs i2i automatically using ``params.reference_images``
        or the ``task`` name.
        """
        api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
        if not api_key:
            raise RuntimeError("Missing DASHSCOPE_API_KEY for Qwen integration.")

        prompt = request.prompt
        if not prompt:
            raise ValueError("Prompt is required for Qwen provider.")

        reference_images: Sequence[str] = request.params.get("reference_images") or []
        is_image_to_image = bool(reference_images) or request.task == "image2image"

        model = request.params.get("model") or (
            "wan2.5-i2i-preview" if is_image_to_image else "wan2.5-t2i-preview"
        )
        num_outputs = int(request.params.get("num_outputs") or request.params.get("num_variations") or 1)
        style = request.params.get("style") or "<auto>"

        requested_size = request.size or "1024x1024"
        width_px, height_px = self._parse_size(requested_size)
        resolved_width, resolved_height = self._resolve_dimensions(
            width_px,
            height_px,
            model=model,
        )
        size = self._format_size(resolved_width, resolved_height)
        if (width_px, height_px) != (resolved_width, resolved_height):
            logger.debug(
                "Qwen adjusted size from %sx%s to %sx%s for model=%s",
                width_px,
                height_px,
                resolved_width,
                resolved_height,
                model,
            )

        if is_image_to_image:
            images_payload = [self._encode_reference(item) for item in reference_images]
            payload = {
                "model": model,
                "input": {
                    "prompt": prompt,
                    "images": images_payload,
                },
                "parameters": {
                    "n": max(1, min(num_outputs, 4)),
                },
            }
            submit_url = request.params.get("endpoint", self.image_to_image_endpoint)
        else:
            payload = {
                "model": model,
                "input": {"prompt": prompt},
                "parameters": {
                    "size": size,
                    "n": max(1, min(num_outputs, 4)),
                    "style": style,
                },
            }
            submit_url = request.params.get("endpoint", self.submit_endpoint)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }

        timeout = httpx.Timeout(self.timeout_seconds)

        logger.info(
            "Calling Qwen image API (mode=%s) model=%s size=%s",
            "i2i" if is_image_to_image else "t2i",
            model,
            size,
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                submit_resp = await client.post(submit_url, json=payload, headers=headers)
                submit_resp.raise_for_status()
            except httpx.HTTPStatusError as exc:  # noqa: PERF203
                details = exc.response.text if exc.response is not None else str(exc)
                raise RuntimeError(f"Qwen submission failed: {details}") from exc

            submit_body = submit_resp.json()

            task_id = self._extract_task_id(submit_body)
            if not task_id:
                raise RuntimeError(f"Failed to obtain task_id from Qwen response: {submit_body}")

            poll_headers = {"Authorization": headers["Authorization"]}
            images = await self._poll_results(
                client=client,
                task_id=task_id,
                headers=poll_headers,
            )

        metadata: Dict[str, Any] = {
            "provider": self.name,
            "model": model,
            "size": size,
            "style": style if not is_image_to_image else None,
            "mode": "image2image" if is_image_to_image else "text2image",
            "task_id": task_id,
        }

        return {
            "status": "success",
            "task_id": str(request.task_id or uuid4()),
            "images": images,
            "image_url": images[0] if images else "",
            "metadata": metadata,
        }

    async def _poll_results(
        self,
        *,
        client: httpx.AsyncClient,
        task_id: str,
        headers: Dict[str, str],
    ) -> list[str]:
        """Poll DashScope task endpoint until images are returned."""
        elapsed = 0.0
        poll_url = self.task_endpoint.format(task_id=task_id)
        while elapsed <= self.poll_timeout:
            response = await client.get(poll_url, headers=headers)
            response.raise_for_status()
            body = response.json()
            output = body.get("output") or {}
            status = (output.get("task_status") or body.get("status") or "").upper()

            if status == "SUCCEEDED":
                results = output.get("results") or []
                images = []
                for item in results:
                    if item.get("url"):
                        images.append(item["url"])
                    elif item.get("b64_json"):
                        images.append(self._to_data_url(item["b64_json"]))
                return images

            if status == "FAILED":
                raise RuntimeError(f"Qwen task failed: {body}")

            await asyncio.sleep(self.poll_interval)
            elapsed += self.poll_interval

        raise RuntimeError("Qwen task polling timed out")

    def _format_size(self, width: int, height: int) -> str:
        """Format width/height into DashScope expected 'W*H' string."""
        return f"{width}*{height}"

    def _parse_size(self, size: str) -> Tuple[int, int]:
        """Parse WxH or W*H strings into integers."""
        token = size.lower().replace("x", "*")
        try:
            width_str, height_str = token.split("*", 1)
            width = max(1, int(width_str.strip()))
            height = max(1, int(height_str.strip()))
        except (ValueError, AttributeError):
            logger.warning("无法解析尺寸 %s，使用默认 1024x1024", size)
            return (1024, 1024)
        return (width, height)

    def _resolve_dimensions(self, width: int, height: int, *, model: str) -> Tuple[int, int]:
        """Pick a supported output size for the requested model."""
        ratio_key = self._match_ratio(width, height)
        model_lower = (model or "").lower()

        qwen_fixed_sizes: Dict[str, Tuple[int, int]] = {
            "1:1": (1328, 1328),
            "16:9": (1664, 928),
            "9:16": (928, 1664),
            "4:3": (1472, 1140),
            "3:4": (1140, 1472),
        }
        wan_default_sizes: Dict[str, Tuple[int, int]] = {
            "1:1": (1024, 1024),
            "16:9": (1440, 810),
            "9:16": (810, 1440),
            "4:3": (1440, 1080),
            "3:4": (1080, 1440),
        }

        if "wan" in model_lower or "wanxiang" in model_lower:
            return wan_default_sizes.get(ratio_key, wan_default_sizes["1:1"])
        return qwen_fixed_sizes.get(ratio_key, qwen_fixed_sizes["1:1"])

    def _match_ratio(self, width: int, height: int) -> str:
        """Approximate common aspect ratios."""
        if height == 0:
            return "1:1"
        ratio = width / height
        ratio_map: Dict[str, float] = {
            "1:1": 1.0,
            "16:9": 16 / 9,
            "9:16": 9 / 16,
            "4:3": 4 / 3,
            "3:4": 3 / 4,
        }
        best = "1:1"
        best_delta = float("inf")
        for key, target in ratio_map.items():
            delta = abs(ratio - target)
            if delta < best_delta:
                best = key
                best_delta = delta
        return best

    def _extract_task_id(self, body: Dict[str, Any]) -> Optional[str]:
        """Extract task id from a submission response body."""
        output = body.get("output")
        if isinstance(output, dict) and output.get("task_id"):
            return output["task_id"]
        return body.get("task_id")

    def _to_data_url(self, b64_payload: str) -> str:
        """Prefix raw base64 payload as PNG data URL if needed."""
        if b64_payload.startswith("data:"):
            return b64_payload
        return f"data:image/png;base64,{b64_payload}"

    def _encode_reference(self, image: str) -> Any:
        """Coerce a reference image to API expected format (URL or base64)."""
        if image.startswith("data:"):
            _, _, encoded = image.partition(",")
            compressed = self._compress_base64_if_needed(encoded)
            return {"image_base64": compressed}
        return image

    def _compress_base64_if_needed(self, encoded: str) -> str:
        """Reduce base64 images that would exceed DashScope payload limits."""
        try:
            raw = base64.b64decode(encoded, validate=False)
        except Exception:  # noqa: BLE001
            logger.warning("Failed to decode base64 reference image; sending original payload.")
            return encoded

        original_size = len(raw)
        if original_size <= self.max_reference_image_bytes:
            return encoded

        compressed = self._compress_image_bytes(raw, max_bytes=self.max_reference_image_bytes)
        if compressed is None:
            logger.warning("Reference image compression failed; falling back to original bytes.")
            return encoded

        logger.info(
            "Compressed reference image from %.2fMB to %.2fMB",
            original_size / (1024 * 1024),
            len(compressed) / (1024 * 1024),
        )
        return base64.b64encode(compressed).decode("utf-8")

    def _compress_image_bytes(self, image_bytes: bytes, *, max_bytes: int) -> Optional[bytes]:
        """Iteratively downscale/adjust quality until under the byte limit."""
        try:
            with Image.open(BytesIO(image_bytes)) as img:
                img = img.convert("RGB")

                # First try reducing JPEG quality.
                for quality in (85, 75, 65, 55, 50):
                    buffer = BytesIO()
                    img.save(buffer, format="JPEG", quality=quality, optimize=True)
                    if buffer.tell() <= max_bytes:
                        return buffer.getvalue()

                # If still too large, progressively downscale and retry.
                width, height = img.size
                while width > 256 and height > 256:
                    width = int(width * 0.8)
                    height = int(height * 0.8)
                    resized = img.resize((max(1, width), max(1, height)), Image.LANCZOS)
                    for quality in (80, 70, 60, 50):
                        buffer = BytesIO()
                        resized.save(buffer, format="JPEG", quality=quality, optimize=True)
                        if buffer.tell() <= max_bytes:
                            return buffer.getvalue()

                # Final attempt with aggressive compression.
                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=40, optimize=True)
                if buffer.tell() <= max_bytes:
                    return buffer.getvalue()
                return None

        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to process reference image for compression: %s", exc)
            return None
