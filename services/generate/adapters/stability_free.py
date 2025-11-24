from __future__ import annotations

import os
import uuid
from typing import Any, Dict

import httpx

from services.generate.adapters.base import BaseProvider
from services.generate.models import GenerateRequestPayload


class StabilityFreeProvider(BaseProvider):
    """Stability AI 免费额度接口。"""

    name = "stability_free"
    endpoint = "https://api.stability.ai/v2beta/stable-image/generate/core"

    async def generate(self, request: GenerateRequestPayload) -> Dict[str, Any]:
        api_key = os.getenv("STABILITY_KEY")
        headers = {
            "Authorization": f"Bearer {api_key}" if api_key else "",
        }
        form_data = {
            "prompt": request.prompt,
            "aspect_ratio": request.params.get("aspect_ratio", "1:1"),
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.endpoint,
                headers=headers,
                data=form_data,
            )
            response.raise_for_status()
            data = response.json()

        image_url = data.get("url") if isinstance(data, dict) else None

        return {
            "status": "success" if image_url else "error",
            "task_id": str(request.task_id or uuid.uuid4()),
            "image_url": image_url,
            "metadata": {
                "provider": self.name,
                "cost": 0,
                "duration": None,
            },
        }
