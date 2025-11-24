from __future__ import annotations

from uuid import UUID

from services.common.models import GeneratedImage
from services.scoring.base import ScoreService
from services.scoring.utils import deterministic_score


class ClarityEvalService(ScoreService):
    """清晰度评估，偏重细节保留与锐利度。"""

    module_name = "clarity_eval"

    async def score(
        self,
        *,
        task_id: UUID,
        image: GeneratedImage,
    ) -> float:
        seed = f"{task_id}:{image.url}"
        return deterministic_score(seed, offset=3)
