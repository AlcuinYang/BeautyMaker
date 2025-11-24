from __future__ import annotations

from uuid import UUID

from services.common.models import GeneratedImage
from services.scoring.base import ScoreService
from services.scoring.utils import deterministic_score


class NoiseEvalService(ScoreService):
    """噪声评估，数值越高代表噪点越少。"""

    module_name = "noise_eval"

    async def score(
        self,
        *,
        task_id: UUID,
        image: GeneratedImage,
    ) -> float:
        seed = f"{task_id}:{image.url}"
        raw = deterministic_score(seed, offset=4)
        return round(1 - raw, 3)
