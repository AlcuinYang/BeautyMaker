from __future__ import annotations

import os
import uuid
from typing import Any, Dict

from services.generate.adapters.base import BaseProvider
from services.generate.models import GenerateRequestPayload


class GeminiFlashProvider(BaseProvider):
    """Google Gemini 2.5 Flash Image 适配器。"""

    name = "gemini_2_5"
    model_name = "gemini-2.5-flash-image-preview"

    async def generate(self, request: GenerateRequestPayload) -> Dict[str, Any]:
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        model = genai.GenerativeModel(self.model_name)
        result = model.generate_images(request.prompt)
        image_url = ""
        if getattr(result, "generated_images", None):
            image_url = result.generated_images[0].uri

        return {
            "status": "success",
            "task_id": str(request.task_id or uuid.uuid4()),
            "image_url": image_url,
            "metadata": {
                "provider": self.name,
                "cost": None,
                "duration": None,
            },
        }
