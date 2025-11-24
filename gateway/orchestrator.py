from __future__ import annotations

import logging
from typing import Dict, Optional
from uuid import uuid4

from gateway.schemas import GenerateRequest, GenerateResponse
from services.enhancer.service import EnhancementService
from services.generate.service import GenerationService
from services.scoring.aggregator import AggregationResult, ScoringAggregator
from services.selector.service import SelectorService

logger = logging.getLogger(__name__)


def _public_scores(module_scores: Dict[str, float]) -> Dict[str, float]:
    """Expose only the holistic (MNet) score for front-end display."""
    if "holistic" in module_scores and module_scores["holistic"] is not None:
        return {"holistic": module_scores["holistic"]}
    return {}


class ServiceOrchestrator:
    """负责协调生成、评分、增强与选图的核心编排器。"""

    def __init__(
        self,
        generation_service: GenerationService,
        scoring_aggregator: ScoringAggregator,
        enhancer: EnhancementService,
        selector: SelectorService,
    ) -> None:
        self._generation_service = generation_service
        self._scoring_aggregator = scoring_aggregator
        self._enhancer = enhancer
        self._selector = selector

    async def handle_generate(self, payload: GenerateRequest) -> GenerateResponse:
        """执行完整流程：生成 → 增强 → 评分 → 选图 → 返回结果。"""
        task_id = uuid4()
        logger.info("Handling generate request", extra={"task_id": str(task_id)})

        generation_result = await self._generation_service.generate(
            task_id=task_id, request=payload
        )
        logger.debug(
            "Generation completed",
            extra={"task_id": str(task_id), "image_count": len(generation_result.images)},
        )

        processed_images = generation_result.images
        if payload.enhancement.apply_clarity:
            processed_images = await self._enhancer.apply_clarity(
                task_id=task_id, images=processed_images
            )

        scoring_summary: Optional[AggregationResult] = None
        if processed_images and payload.use_modules:
            scoring_summary = await self._scoring_aggregator.score_candidates(
                task_id=task_id,
                images=processed_images,
                modules=payload.use_modules,
            )

        selection = await self._selector.select_best(
            task_id=task_id,
            candidates=processed_images,
            evaluations=scoring_summary.image_results if scoring_summary else None,
        )

        modules_used = scoring_summary.modules_used if scoring_summary else []
        final_scores = {}
        composite_score: Optional[float] = None
        if selection.evaluation:
            final_scores = _public_scores(selection.evaluation.module_scores)
            composite_score = selection.evaluation.composite_score

        return GenerateResponse(
            status="success",
            task_id=task_id,
            image_url=selection.image.url,
            modules_used=modules_used,
            scores=final_scores,
            composite_score=composite_score,
            best_candidate=selection.image.url,
        )
