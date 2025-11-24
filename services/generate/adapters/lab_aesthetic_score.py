from __future__ import annotations

from typing import Any, Dict

from services.generate.adapters.base import BaseProvider
from services.generate.models import GenerateRequestPayload


class LabAestheticScoreProvider(BaseProvider):
    """实验室美学评分模型占位。"""

    name = "lab_aesthetic_score"

    async def generate(self, request: GenerateRequestPayload) -> Dict[str, Any]:
        return {
            "status": "pending",
            "task_id": "lab_score_placeholder",
            "metadata": {
                "provider": self.name,
                "message": "Laboratory aesthetic scoring integration pending.",
            },
        }
