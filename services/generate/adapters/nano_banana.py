from __future__ import annotations

import os
import uuid
from typing import Any, Dict

import httpx

from services.generate.adapters.base import BaseProvider
from services.generate.models import GenerateRequestPayload


class NanoBananaProvider(BaseProvider):
    """Fal.ai Nano Banana 模型适配器。"""

    name = "nano_banana"
    endpoint = "https://fal.run/fal-ai/nano-banana"

    async def generate(self, request: GenerateRequestPayload) -> Dict[str, Any]:
        api_key = os.getenv("FAL_KEY")
        headers = {"Authorization": f"Key {api_key}"} if api_key else {}
        payload = {"input": request.prompt}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        image_url = data.get("image", "")

        return {
            "status": "success",
            "task_id": str(request.task_id or uuid.uuid4()),
            "image_url": image_url,
            "metadata": {
                "provider": self.name,
                "cost": data.get("cost"),
                "duration": data.get("latency"),
            },
        }
