from __future__ import annotations

import base64
import logging
import os
import random
from typing import Any, Dict, List, Tuple
from urllib.parse import quote_plus
from uuid import uuid4

import httpx

from services.generate.adapters.base import BaseProvider
from services.generate.models import GenerateRequestPayload

logger = logging.getLogger(__name__)


class PollinationsProvider(BaseProvider):
    """Pollinations 免费文生图服务，服务端代理获取图片并返回 data URL。"""

    name = "pollinations"
    base_url = "https://image.pollinations.ai/prompt"
    max_outputs = 4  # 避免免费接口过载
    timeout_seconds = 45.0

    async def generate(self, request: GenerateRequestPayload) -> Dict[str, Any]:
        if not request.prompt:
            raise ValueError("Prompt is required for Pollinations provider.")

        width, height = self._resolve_dimensions(request.size)
        num_outputs = self._resolve_num_outputs(request.params)
        model = request.params.get("model") or "flux"
        referrer = request.params.get("referrer") or "aesthetic-engine.local"

        prompt = request.prompt
        images: List[str] = []
        seeds: List[str] = []
        sources: List[str] = []

        proxy_url = os.getenv("GLOBAL_HTTP_PROXY")
        timeout = httpx.Timeout(self.timeout_seconds)
        transport = httpx.AsyncHTTPTransport(proxy=proxy_url) if proxy_url else None

        async with httpx.AsyncClient(timeout=timeout, transport=transport) as client:
            for _ in range(num_outputs):
                seed = request.params.get("seed") or self._random_seed()
                seeds.append(seed)
                source_url = self._build_image_url(
                    prompt=prompt,
                    width=width,
                    height=height,
                    seed=seed,
                    model=model,
                    referrer=referrer,
                )
                sources.append(source_url)
                try:
                    data_url = await self._fetch_as_data_url(client, source_url)
                    images.append(data_url)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Pollinations fetch failed: %s", exc)
                    images.append("")

        return {
            "status": "success",
            "task_id": str(request.task_id or uuid4()),
            "images": images,
            "image_url": next((img for img in images if img), ""),
            "metadata": {
                "provider": self.name,
                "width": width,
                "height": height,
                "model": model,
                "seeds": seeds,
                "source_urls": sources,
            },
        }

    async def _fetch_as_data_url(self, client: httpx.AsyncClient, url: str) -> str:
        response = await client.get(url, headers={"Accept": "image/*"})
        response.raise_for_status()

        content_type = response.headers.get("content-type", "image/png")
        encoded = base64.b64encode(response.content).decode("utf-8")
        return f"data:{content_type};base64,{encoded}"

    def _resolve_dimensions(self, size: str | None) -> Tuple[int, int]:
        default = (1024, 1024)
        if not size or "x" not in size:
            return default
        try:
            w, h = map(int, size.lower().split("x", 1))
            return (max(64, w), max(64, h))
        except Exception:
            return default

    def _resolve_num_outputs(self, params: Dict[str, Any]) -> int:
        raw = params.get("num_outputs") or params.get("n") or 1
        try:
            return max(1, min(self.max_outputs, int(raw)))
        except Exception:
            return 1

    def _random_seed(self) -> str:
        return str(random.randint(0, 2**31 - 1))

    def _build_image_url(
        self,
        *,
        prompt: str,
        width: int,
        height: int,
        seed: str,
        model: str,
        referrer: str,
    ) -> str:
        encoded_prompt = quote_plus(prompt)
        query_params = {
            "width": width,
            "height": height,
            "seed": seed,
            "model": model,
            "referrer": referrer,
        }
        query = "&".join(
            f"{key}={quote_plus(str(value))}" for key, value in query_params.items() if value is not None
        )
        return f"{self.base_url}/{encoded_prompt}?{query}" if query else f"{self.base_url}/{encoded_prompt}"
