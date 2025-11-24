from __future__ import annotations

from uuid import UUID

from services.common.models import GeneratedImage
from services.scoring.base import ScoreService
from services.scoring.utils import deterministic_score


class ColorScoreService(ScoreService):
    """色彩相关的占位评分模块，返回稳定的伪随机分数。"""

    module_name = "color_score"

    async def score(
        self,
        *,
        task_id: UUID,
        image: GeneratedImage,
    ) -> float:
        seed = f"{task_id}:{image.url}"
        return deterministic_score(seed, offset=1)
