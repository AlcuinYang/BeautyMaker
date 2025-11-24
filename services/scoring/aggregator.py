from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence
from uuid import UUID

from services.common.models import GeneratedImage
from services.scoring.base import ScoreService
from services.scoring.clarity_eval.service import ClarityEvalService
from services.scoring.contrast_score.service import ContrastScoreService
from services.scoring.color_score.service import ColorScoreService
from services.scoring.holistic.doubao_client import DoubaoAestheticClient, DoubaoAestheticResult
from services.scoring.holistic.service import HolisticScoreService
from services.scoring.noise_eval.service import NoiseEvalService
from services.scoring.quality_score.service import QualityScoreService


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ImageEvaluation:
    """单张图片的评分汇总。"""

    module_scores: Dict[str, float]
    composite_score: float
    module_comments: Optional[Dict[str, str]] = None
    


@dataclass(slots=True)
class AggregationResult:
    """汇总结果，包含每张图片的评分及实际使用的模块列表。"""

    image_results: Dict[str, ImageEvaluation]
    modules_used: List[str]


class ScoringAggregator:
    """Runs scoring services and exposes holistic score as composite."""

    def __init__(
        self,
        services: Iterable[ScoreService] | None = None,
    ) -> None:
        default_services: Sequence[ScoreService] = services or (
            HolisticScoreService(),
            ColorScoreService(),
            ContrastScoreService(),
            ClarityEvalService(),
            NoiseEvalService(),
            QualityScoreService(),
        )
        self._services_map = {service.module_name: service for service in default_services}
        self._doubao_client = DoubaoAestheticClient()

    async def score_candidates(
        self,
        *,
        task_id: UUID,
        images: Iterable[GeneratedImage],
        modules: Sequence[str],
    ) -> AggregationResult:
        services = self._select_services(modules)
        result: Dict[str, ImageEvaluation] = {}
        modules_union: set[str] = set()
        for image in images:
            score_map, comments = await self._score_single(
                task_id=task_id, image=image, services=services
            )
            modules_union.update(score_map.keys())
            result[image.url] = ImageEvaluation(
                module_scores=score_map,
                composite_score=self._primary_score(score_map),
                module_comments=comments if comments else None,
            )

        return AggregationResult(
            image_results=result,
            modules_used=sorted(modules_union),
        )

    async def _score_single(
        self,
        *,
        task_id: UUID,
        image: GeneratedImage,
        services: Sequence[ScoreService],
    ) -> tuple[Dict[str, float], Dict[str, str]]:
        async def run(service: ScoreService) -> float:
            return await service.score(task_id=task_id, image=image)

        module_scores: Dict[str, float] = {}
        module_comments: Dict[str, str] = {}
        requested_modules = {service.module_name for service in services}

        doubao_result = await self._fetch_doubao_scores(image=image)
        if doubao_result:
            for module_name, value in doubao_result.scores.items():
                if not requested_modules or module_name in requested_modules:
                    module_scores[module_name] = value
            for module_name, comment in doubao_result.comments.items():
                if not requested_modules or module_name in requested_modules:
                    module_comments[module_name] = comment

        tasks: list[asyncio.Task[float]] = []
        services_to_run: list[ScoreService] = []
        for service in services:
            if service.module_name in module_scores:
                continue
            services_to_run.append(service)
            tasks.append(asyncio.create_task(run(service)))

        if tasks:
            raw_scores = await asyncio.gather(*tasks)
            for service, score in zip(services_to_run, raw_scores):
                module_scores[service.module_name] = score

        return module_scores, module_comments

    def _primary_score(self, module_scores: Dict[str, float]) -> float:
        """Return holistic/MNet score if available, otherwise fall back to 0."""
        value = module_scores.get("holistic")
        if value is None:
            return 0.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _select_services(self, modules: Sequence[str]) -> Sequence[ScoreService]:
        """根据请求指定的模块筛选可用服务，默认退回全部。"""
        if not modules:
            return tuple(self._services_map.values())

        selected = []
        for module in modules:
            service = self._services_map.get(module)
            if service:
                selected.append(service)

        if not selected:
            return tuple(self._services_map.values())
        return tuple(selected)

    async def _fetch_doubao_scores(self, image: GeneratedImage) -> Optional[DoubaoAestheticResult]:
        try:
            return await self._doubao_client.evaluate(image=image)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Doubao aesthetic evaluation failed: %s", exc)
            return None
