from __future__ import annotations

import os
import uuid
from typing import Any, Dict

import httpx

from services.generate.adapters.base import BaseProvider
from services.generate.models import GenerateRequestPayload


class HuggingFaceProvider(BaseProvider):
    """Hugging Face Inference API 适配器。"""

    name = "huggingface"
    model_endpoint = (
        "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
    )

    async def generate(self, request: GenerateRequestPayload) -> Dict[str, Any]:
        token = os.getenv("HF_TOKEN")
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        payload: Dict[str, Any] = {"inputs": request.prompt}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.model_endpoint,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        image_url = ""
        if isinstance(data, list) and data:
            image_url = data[0].get("generated_image_url", "")

        return {
            "status": "success",
            "task_id": str(request.task_id or uuid.uuid4()),
            "image_url": image_url,
            "metadata": {
                "provider": self.name,
                "cost": 0,
                "duration": None,
            },
        }
