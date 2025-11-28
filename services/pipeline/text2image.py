"""Text-to-image smart pipeline.

This module orchestrates the t2i flow end to end:

1) Optional prompt expansion (LLM stub today)
2) Parallel candidate generation across selected providers
3) Multi-module aesthetic scoring with holistic-as-composite
4) Selection of the best candidate
5) Optional response decoration for UI (summary, per-candidate details)

The public entrypoint is ``run_text2image_pipeline`` which receives a
``Text2ImagePipelineRequest`` pydantic model and returns a plain dict that
is easy to serialize via FastAPI. All helper functions are small and focused
to keep the orchestration legible and testable.
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any, Dict, List, Optional, Sequence, Tuple
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from services.common.models import ComparativeReview, GeneratedImage
from services.generate import get_provider
from services.generate.models import GenerateRequestPayload
from services.reviewer.service import AestheticReviewer
from services.scoring.aggregator import AggregationResult, ImageEvaluation, ScoringAggregator
from services.selector.service import SelectorService

logger = logging.getLogger(__name__)


DEFAULT_PROVIDERS: Sequence[str] = ("doubao_seedream",)

DEFAULT_MODULES = [
    "holistic",
    "color_score",
    "contrast_score",
    "clarity_eval",
    "noise_eval",
    "quality_score",
]


class PipelineParams(BaseModel):
    """Optional knobs for the t2i pipeline.

    - ratio: aspect ratio string that later maps to a concrete size.
    - expand_prompt: whether to add style keywords to the user prompt.
    - modules: scoring module overrides; falls back to DEFAULT_MODULES.
    """
    ratio: str = Field(default="1:1")
    expand_prompt: bool = Field(default=False)
    modules: Optional[List[str]] = None


class Text2ImagePipelineRequest(BaseModel):
    """Request model for the smart t2i pipeline.

    providers: one or more provider ids; the legacy ``provider`` field is
    kept for backward compatibility and folded into ``providers``.
    reference_images: optional list of reference image URLs or base64 strings
    to guide generation (supported by Seedream 4.0, Wanx i2i).
    """
    prompt: str
    providers: List[str] = Field(default_factory=list, min_length=1, max_length=4)
    provider: Optional[str] = Field(default=None, exclude=True)
    num_candidates: int = Field(default=3, ge=1, le=6)
    reference_images: Optional[List[str]] = Field(default=None, max_length=10)
    params: PipelineParams = Field(default_factory=PipelineParams)

    @model_validator(mode="after")
    def ensure_providers(self) -> "Text2ImagePipelineRequest":
        if not self.providers:
            if self.provider:
                self.providers = [self.provider]
            else:
                self.providers = list(DEFAULT_PROVIDERS)
        self.providers = [provider for provider in self.providers if provider]
        if not self.providers:
            raise ValueError("提供的模型标识不可为空。")
        return self


class Text2ImagePipelineResponse(BaseModel):
    """Response model for the text2image pipeline.

    Includes the best image, scores, candidates, and optionally a comparative review
    explaining why the best image was selected over the lowest-scoring one.
    """
    status: str = Field(description="Execution status: 'success' or 'failed'")
    task_id: str = Field(description="Unique task identifier")
    best_image_url: Optional[str] = Field(default=None, description="URL of the selected best image")
    best_composite_score: Optional[float] = Field(default=None, description="Composite aesthetic score (0-1)")
    candidates: List[Dict[str, Any]] = Field(default_factory=list, description="All candidate images with scores")
    summary: Optional[str] = Field(default=None, description="Summary of the best image's aesthetic qualities")
    prompt: Optional[Dict[str, Any]] = Field(default=None, description="Prompt details (original, applied, expanded)")
    providers_used: List[str] = Field(default_factory=list, description="Provider IDs used in generation")
    review: Optional[ComparativeReview] = Field(
        default=None,
        description="Comparative review explaining why the best image won (only when multiple candidates exist)"
    )
    message: Optional[str] = Field(default=None, description="Error message if status is 'failed'")


async def run_text2image_pipeline(payload: Text2ImagePipelineRequest) -> Dict[str, Any]:
    """High-level entry that runs the full t2i orchestration."""

    task_id = uuid4()
    try:
        applied_prompt, expansion_suffix = await _maybe_expand_prompt(
            prompt=payload.prompt,
            enable=payload.params.expand_prompt,
        )

        candidates = await _generate_candidates(
            provider_names=payload.providers,
            prompt=applied_prompt,
            size=_ratio_to_size(payload.params.ratio),
            params={"ratio": payload.params.ratio},
            num_candidates=payload.num_candidates,
            reference_images=payload.reference_images,
        )

        if not candidates:
            raise RuntimeError("生成阶段未返回任何候选图片")

        aggregation = await _evaluate_candidates(
            task_id=task_id,
            images=candidates,
            modules=payload.params.modules or DEFAULT_MODULES,
        )

        selection = await _select_best(task_id=task_id, candidates=candidates, aggregation=aggregation)

        best_image = selection.image

        best_evaluation = aggregation.image_results.get(best_image.url) if aggregation else None

        # Generate comparative review if we have multiple candidates
        review = None
        if aggregation and len(candidates) > 1:
            reviewer = AestheticReviewer()
            review_result = await reviewer.review_candidates(candidates, aggregation.image_results)
            if review_result:
                review = review_result.model_dump()

        response = {
            "status": "success",
            "task_id": str(task_id),
            "best_image_url": best_image.url,
            "best_composite_score": best_evaluation.composite_score if best_evaluation else None,
            "candidates": _serialize_candidates(candidates, aggregation),
            "summary": _build_summary(best_evaluation),
            "prompt": {
                "original": payload.prompt,
                "applied": applied_prompt,
                "expanded": applied_prompt if payload.params.expand_prompt else None,
                "expansion_suffix": expansion_suffix,
            },
            "providers_used": sorted({image.provider for image in candidates}),
        }

        # Add review if available
        if review:
            response["review"] = review

        return response

    except Exception as exc:  # noqa: BLE001
        logger.exception("Pipeline execution failed: %s", exc)
        return {
            "status": "failed",
            "task_id": str(task_id),
            "message": str(exc),
        }


async def _maybe_expand_prompt(prompt: str, enable: bool) -> Tuple[str, Optional[str]]:
    """Prompt expansion is temporarily disabled and returns the original prompt."""
    return prompt, None


async def _generate_candidates(
    *,
    provider_names: Sequence[str],
    prompt: str,
    size: str,
    params: Dict[str, Any],
    num_candidates: int,
    reference_images: Optional[List[str]] = None,
) -> List[GeneratedImage]:
    """Generate candidates in parallel across providers and n-variations.

    Returns a uniform list of ``GeneratedImage`` items that include provider
    name, url and basic metadata, filtering out failed tasks.

    If reference_images is provided, automatically switches to image2image task
    for providers that support it (Seedream 4.0, Wanx i2i).
    """
    provider_limits: Dict[str, asyncio.Semaphore] = {
        name: asyncio.Semaphore(1) for name in set(provider_names)
    }

    async def _run_with_retry(
        *,
        provider_label: str,
        semaphore: asyncio.Semaphore,
        runner,
    ) -> GeneratedImage:
        delays = [0.3, 0.8, 1.5]
        last_error: Optional[Exception] = None
        for attempt, delay in enumerate(delays, start=1):
            try:
                async with semaphore:
                    # Small spacing to avoid bursting provider rate limits
                    await asyncio.sleep(0.1 + random.uniform(0, 0.1))
                    return await runner()
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                should_retry = _is_retryable_generation_error(exc)
                if attempt < len(delays) and should_retry:
                    backoff = delay + random.uniform(0, 0.2)
                    logger.warning(
                        "生成候选重试(provider=%s attempt=%s/%s): %s，%.2fs 后再试",
                        provider_label,
                        attempt,
                        len(delays),
                        exc,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    continue
                raise
        assert last_error  # for type checkers
        raise last_error

    async def _generate_single(provider_id: str) -> GeneratedImage:
        provider = get_provider(provider_id)
        task = "image2image" if reference_images else "text2image"
        semaphore = provider_limits[provider_id]

        # Merge reference_images into params
        generation_params = {**params}
        if reference_images:
            generation_params["reference_images"] = reference_images

        async def _execute() -> GeneratedImage:
            request_payload = GenerateRequestPayload(
                task=task,
                prompt=prompt,
                provider=provider.name,
                size=size,
                params=generation_params,
            )
            result = await provider.generate(request_payload)
            image_urls = _ensure_list(result.get("images"))
            if result.get("image_url"):
                image_urls.append(result["image_url"])

            image_urls = [url for url in image_urls if isinstance(url, str) and url]
            if not image_urls:
                raise RuntimeError("提供方未返回有效的图片地址")

            return GeneratedImage(
                url=image_urls[0],
                provider=provider.name,
                prompt=prompt,
                metadata=result.get("metadata", {}),
            )

        return await _run_with_retry(
            provider_label=provider.name,
            semaphore=semaphore,
            runner=_execute,
        )

    tasks: List[asyncio.Task[GeneratedImage]] = []
    for provider_name in provider_names:
        for _ in range(num_candidates):
            tasks.append(asyncio.create_task(_generate_single(provider_name)))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    images: List[GeneratedImage] = []
    for item in results:
        if isinstance(item, Exception):
            logger.warning("生成候选失败: %s", item)
            continue
        images.append(item)
    return images


async def _evaluate_candidates(
    *,
    task_id: UUID,
    images: List[GeneratedImage],
    modules: List[str],
) -> Optional[AggregationResult]:
    """Score the given candidates with the configured scoring modules."""
    if not images:
        return None
    aggregator = ScoringAggregator()
    return await aggregator.score_candidates(task_id=task_id, images=images, modules=modules)


async def _select_best(
    *,
    task_id: UUID,
    candidates: List[GeneratedImage],
    aggregation: Optional[AggregationResult],
):
    """Select the best candidate using holistic composite score."""
    selector = SelectorService()
    evaluations = aggregation.image_results if aggregation else None
    return await selector.select_best(task_id=task_id, candidates=candidates, evaluations=evaluations)


def _serialize_candidates(
    candidates: List[GeneratedImage],
    aggregation: Optional[AggregationResult],
) -> List[Dict[str, Any]]:
    """Build a UI-friendly list for candidate panel.

    Holistic score is intentionally not exposed per the product spec; it is
    used only as the composite ranking metric and reported separately.
    """
    payload: List[Dict[str, Any]] = []
    for image in candidates:
        record: Dict[str, Any] = {
            "image_url": image.url,
            "provider": image.provider,
        }
        evaluation = aggregation.image_results.get(image.url) if aggregation else None
        if evaluation:
            visible_scores = {
                name: score for name, score in evaluation.module_scores.items() if name != "holistic"
            }
            if visible_scores:
                record["scores"] = visible_scores
            record["composite_score"] = evaluation.composite_score
        payload.append(record)
    return payload


LABEL_MAP_FOR_SUMMARY = {
    "color_score": "艺术美感",
    "contrast_score": "物理逻辑",
    "clarity_eval": "结构合理性",  # Critical mapping change
    "noise_eval": "画面纯净度",
    "quality_score": "语义忠实度",
    "holistic": "综合评分",
}


def _build_summary(evaluation) -> str:
    if not evaluation:
        return "生成完成。"

    comments = getattr(evaluation, "module_comments", None) or {}
    if comments:
        ordered_keys = [
            "contrast_score",
            "color_score",
            "clarity_eval",
            "quality_score",
            "noise_eval",
        ]
        summary_parts: List[str] = []
        for key in ordered_keys:
            comment = comments.get(key)
            if comment:
                label = LABEL_MAP_FOR_SUMMARY.get(key, key)
                summary_parts.append(f"{label}：{comment}")
        for key, comment in comments.items():
            if comment and key not in ordered_keys:
                label = LABEL_MAP_FOR_SUMMARY.get(key, key)
                summary_parts.append(f"{label}：{comment}")

        holistic = evaluation.module_scores.get("holistic")
        if holistic is not None:
            summary_parts.append(f"综合美感得分约为 {(holistic * 10):.1f}。")

        if summary_parts:
            return "；".join(summary_parts)

    high_scores = [
        name
        for name, score in evaluation.module_scores.items()
        if name != "holistic" and score is not None and score >= 0.8
    ]
    if not high_scores:
        return "该图片在多个维度表现均衡。"
    readable = ",".join(LABEL_MAP_FOR_SUMMARY.get(name, name) for name in high_scores)
    return f"该图片在 {readable} 等维度表现突出。"


def _ratio_to_size(ratio: str) -> str:
    mapping = {
        "1:1": "2048x2048",
        "3:4": "1728x2304",
        "4:3": "2304x1728",
        "9:16": "1440x2560",
        "16:9": "2560x1440",
    }
    return mapping.get(ratio, "2048x2048")


def _is_retryable_generation_error(exc: Exception) -> bool:
    message = str(exc).lower()
    retry_signals = [
        "throttling",
        "rate limit",
        "ratequota",
        "too many requests",
        "timeout",
        "timed out",
        "temporarily unavailable",
        "server busy",
        "429",
        "connection reset",
    ]
    return any(signal in message for signal in retry_signals)


def _ensure_list(value) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
