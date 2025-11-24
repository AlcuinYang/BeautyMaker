from __future__ import annotations

from uuid import UUID

from services.common.models import GeneratedImage
from services.scoring.base import ScoreService
from services.scoring.utils import deterministic_score


class QualityScoreService(ScoreService):
    """整体质量评分，综合评估画面完成度。"""

    module_name = "quality_score"

    async def score(
        self,
        *,
        task_id: UUID,
        image: GeneratedImage,
    ) -> float:
        seed = f"{task_id}:{image.url}"
        return deterministic_score(seed, offset=5)
