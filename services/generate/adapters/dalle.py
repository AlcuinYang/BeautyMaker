from __future__ import annotations

import os
import uuid
from typing import Any, Dict

from openai import AsyncOpenAI
from services.generate.adapters.base import BaseProvider
from services.generate.models import GenerateRequestPayload


class DalleProvider(BaseProvider):
    """DALL·E 接入占位实现。"""

    name = "dalle"
    model_name = "gpt-image-1"

    async def generate(self, request: GenerateRequestPayload) -> Dict[str, Any]:
        api_key = (
            os.getenv("OPENAI_API_KEY")
            or os.getenv("OPENAI_KEY")
            or os.getenv("OPENAI_TOKEN")
        )
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY for DALL·E integration.")

        client = AsyncOpenAI(api_key=api_key)

        size = request.size or "1024x1024"
        n = max(1, int(request.params.get("num_outputs", 1)))
        quality = request.params.get("quality")
        style = request.params.get("style")

        kwargs: Dict[str, Any] = {
            "model": self.model_name,
            "prompt": request.prompt,
            "size": size,
            "n": n,
            "response_format": "url",
        }
        if quality:
            kwargs["quality"] = quality
        if style:
            kwargs["style"] = style

        response = await client.images.generate(**kwargs)

        image_urls = [
            data.url for data in (response.data or []) if getattr(data, "url", None)
        ]

        metadata = {
            "provider": self.name,
            "model": self.model_name,
            "size": size,
            "created": getattr(response, "created", None),
            "prompt_tokens": getattr(response, "usage", {}).get("prompt_tokens")
            if getattr(response, "usage", None)
            else None,
        }

        return {
            "status": "success" if image_urls else "error",
            "task_id": str(request.task_id or uuid.uuid4()),
            "images": image_urls,
            "metadata": metadata,
        }
