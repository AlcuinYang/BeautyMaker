from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional
from uuid import UUID

from services.common.models import GeneratedImage
from services.scoring.aggregator import ImageEvaluation


@dataclass(slots=True)
class SelectionResult:
    """封装选图结果，便于上层获取评分信息。"""

    task_id: UUID
    image: GeneratedImage
    evaluation: Optional[ImageEvaluation]


class SelectorService:
    """Selects the best candidate image based on scores or heuristics."""

    async def select_best(
        self,
        *,
        task_id: UUID,
        candidates: Iterable[GeneratedImage],
        evaluations: Optional[Dict[str, ImageEvaluation]],
    ) -> SelectionResult:
        candidates = list(candidates)
        if not candidates:
            raise ValueError("No candidates provided for selection.")

        if not evaluations:
            return SelectionResult(task_id=task_id, image=candidates[0], evaluation=None)

        def composite_for(image: GeneratedImage) -> float:
            evaluation = evaluations.get(image.url)
            if evaluation is None:
                return 0.0
            holistic = evaluation.module_scores.get("holistic")
            if holistic is not None:
                return holistic
            return evaluation.composite_score

        best = max(candidates, key=composite_for)
        return SelectionResult(
            task_id=task_id,
            image=best,
            evaluation=evaluations.get(best.url),
        )
