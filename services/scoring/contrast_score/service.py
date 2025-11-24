from __future__ import annotations

from uuid import UUID

from services.common.models import GeneratedImage
from services.scoring.base import ScoreService
from services.scoring.utils import deterministic_score


class ContrastScoreService(ScoreService):
    """对比度评分，衡量明暗层次感。"""

    module_name = "contrast_score"

    async def score(
        self,
        *,
        task_id: UUID,
        image: GeneratedImage,
    ) -> float:
        seed = f"{task_id}:{image.url}"
        return deterministic_score(seed, offset=2)
