"""Image-to-image marketing pipeline (一拍即合).

This pipeline accepts user prompt, one or more reference images, and a set
of providers. It generates candidates, runs aesthetic scoring, and performs
a subject consistency check via Doubao vision understanding. The response
is shaped to serve the frontend UI directly.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence
from uuid import UUID, uuid4

import httpx
from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from pathlib import Path

from services.common.models import GeneratedImage
from services.generate import get_provider
from services.generate.models import GenerateRequestPayload
from services.scoring.aggregator import AggregationResult, ScoringAggregator

logger = logging.getLogger(__name__)

_DOUBAO_LOG_FILE = Path(os.getenv("DOUBAO_LOG_PATH", "logs/doubao_events.jsonl"))
_PIPELINE_LOG_FILE = Path(os.getenv("PIPELINE_LOG_PATH", "logs/pipeline_runs.jsonl"))
DEFAULT_ARK_API_KEY = os.getenv("DEFAULT_ARK_API_KEY", "")


def _record_doubao_event(event: str, payload: Dict[str, Any]) -> None:
    try:
        _DOUBAO_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "event": event,
            "data": payload,
        }
        with _DOUBAO_LOG_FILE.open("a", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False)
            handle.write("\n")
    except Exception:  # noqa: BLE001
        logger.debug("Failed to record Doubao event %s", event, exc_info=True)


def _record_pipeline_event(event: str, payload: Dict[str, Any]) -> None:
    try:
        _PIPELINE_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "event": event,
            "data": payload,
        }
        with _PIPELINE_LOG_FILE.open("a", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False)
            handle.write("\n")
    except Exception:  # noqa: BLE001
        logger.debug("Failed to record pipeline event %s", event, exc_info=True)


DEFAULT_PROVIDERS: Sequence[str] = ("qwen", "doubao_seedream", "dalle")
DEFAULT_MODULES = [
    "holistic",
    "color_score",
    "contrast_score",
    "clarity_eval",
    "noise_eval",
    "quality_score",
]


class Image2ImagePipelineParams(BaseModel):
    """Optional knobs for i2i generation."""
    modules: Optional[List[str]] = None
    image_size: Optional[str] = Field(default=None, pattern=r"^\d+x\d+$")
    num_variations: int = Field(default=1, ge=1, le=15)
    group_mode: bool = False
    platform: Optional[str] = None
    product: Optional[str] = None
    style: Optional[str] = None


class Image2ImagePipelineRequest(BaseModel):
    """Request model for i2i pipeline."""
    prompt: str
    reference_images: List[str] = Field(default_factory=list, min_length=1)
    providers: List[str] = Field(default_factory=list, min_length=1, max_length=4)
    size: str = Field(default="1024x1024", pattern=r"^\d+x\d+$")
    params: Image2ImagePipelineParams = Field(default_factory=Image2ImagePipelineParams)

    @model_validator(mode="after")
    def ensure_providers(self) -> "Image2ImagePipelineRequest":
        if not self.providers:
            self.providers = list(DEFAULT_PROVIDERS[:1])
        self.providers = [provider for provider in self.providers if provider]
        if not self.providers:
            raise ValueError("至少需要选择一个模型进行生成。")
        return self


@dataclass
class GeneratedMarketingImage:
    provider: str
    image: GeneratedImage
    evaluation: Optional[AggregationResult]
    verification: Dict[str, Any]


async def run_image2image_pipeline(payload: Image2ImagePipelineRequest) -> Dict[str, Any]:
    """High-level entry that orchestrates the complete i2i flow."""
    task_id = uuid4()
    logger.info("Running image2image pipeline", extra={"task_id": str(task_id)})

    try:
        modules = payload.params.modules or list(DEFAULT_MODULES)
        size = payload.params.image_size or payload.size

        params = payload.params
        group_mode = bool(getattr(params, "group_mode", False))
        if group_mode:
            modules = ["holistic"]

        final_prompt = payload.prompt

        all_candidates = await _generate_candidates(
            task_id=task_id,
            prompt=final_prompt,
            providers=payload.providers,
            num_variations=payload.params.num_variations,
            reference_images=payload.reference_images,
            modules=modules,
            size=size,
            group_mode=group_mode,
        )

        if not all_candidates:
            raise RuntimeError("生成阶段未返回任何候选图片")

        def _candidate_score(item: GeneratedMarketingImage) -> float:
            evaluation_summary = (
                item.evaluation.image_results.get(item.image.url)
                if item.evaluation
                else None
            )
            return float(evaluation_summary.composite_score) if evaluation_summary else 0.0

        ordered_candidates = (
            sorted(all_candidates, key=_candidate_score, reverse=True)
            if group_mode
            else all_candidates
        )

        results_payload = []
        for candidate in ordered_candidates:
            evaluation_summary = (
                candidate.evaluation.image_results.get(candidate.image.url)
                if candidate.evaluation
                else None
            )
            composite = evaluation_summary.composite_score if evaluation_summary else None
            scores: Dict[str, float] = {}
            if evaluation_summary and not group_mode:
                scores = {
                    key: value
                    for key, value in evaluation_summary.module_scores.items()
                    if key != "holistic"
                }

            results_payload.append(
                {
                    "provider": candidate.provider,
                    "image_url": candidate.image.url,
                    "scores": scores,
                    "composite_score": composite,
                    "verification": candidate.verification,
                    "sequence_index": candidate.image.metadata.get("sequence_index"),
                    "group_size": candidate.image.metadata.get("group_size"),
                }
            )

        best = _select_best_image(all_candidates)
        best_evaluation = (
            best.evaluation.image_results.get(best.image.url)
            if best and best.evaluation
            else None
        )

        feedback_score = best_evaluation.composite_score if best_evaluation else None

        response = {
            "status": "success",
            "task_id": str(task_id),
            "best_image_url": best.image.url if best else None,
            "best_provider": best.provider if best else None,
            "results": results_payload,
            "reference_images": payload.reference_images,
            "image_size": size,
            "providers_used": sorted({item.provider for item in all_candidates}),
            "final_prompt": final_prompt,
            "aesthetic_score": feedback_score,
            "group_mode": group_mode,
        }
        _record_pipeline_event(
            "pipeline_summary",
            {
                "task_id": str(task_id),
                "providers": payload.providers,
                "group_mode": group_mode,
                "best": {
                    "provider": best.provider if best else None,
                    "url": best.image.url if best else None,
                    "aesthetic_score": feedback_score,
                },
                "results": [
                    {
                        "provider": candidate.provider,
                        "url": candidate.image.url,
                        "composite_score": (
                            candidate.evaluation.image_results.get(candidate.image.url).composite_score
                            if candidate.evaluation and candidate.image.url in candidate.evaluation.image_results
                            else None
                        ),
                        "verification": candidate.verification,
                        "sequence_index": candidate.image.metadata.get("sequence_index"),
                        "group_size": candidate.image.metadata.get("group_size"),
                    }
                    for candidate in ordered_candidates
                ],
            },
        )
        return response
    except Exception as exc:  # noqa: BLE001
        logger.exception("Image2Image pipeline failed: %s", exc)
        _record_pipeline_event(
            "pipeline_failed",
            {
                "task_id": str(task_id),
                "error": str(exc),
            },
        )
        return {
            "status": "failed",
            "task_id": str(task_id),
            "message": str(exc),
        }


async def _generate_candidates(
    *,
    task_id: UUID,
    prompt: str,
    providers: Sequence[str],
    num_variations: int,
    reference_images: Sequence[str],
    modules: Sequence[str],
    size: str,
    group_mode: bool,
) -> List[GeneratedMarketingImage]:
    """Generate images across providers for the supplied prompt."""
    aggregator = ScoringAggregator()
    generated: List[GeneratedMarketingImage] = []

    capped_variations = max(1, min(num_variations, 15))

    for provider_id in providers:
        provider = get_provider(provider_id)

        generated_images: List[GeneratedImage] = []

        if provider.name == "doubao_seedream" and capped_variations > 1:
            request_payload = GenerateRequestPayload(
                task="image2image",
                prompt=prompt,
                provider=provider.name,
                size=size,
                params={
                    "reference_images": list(reference_images),
                    "sequential_mode": "auto",
                    "num_variations": capped_variations,
                },
            )
            try:
                response = await provider.generate(request_payload)
                urls = _extract_urls(response)
                if not urls:
                    raise RuntimeError(f"{provider.name} 未返回有效图片")
                metadata_base = response.get("metadata", {}) or {}
                delivered = urls[:capped_variations]
                group_size = len(delivered) if group_mode else None
                logger.info(
                    "Seedream sequential run delivered=%s requested=%s unique=%s",
                    len(delivered),
                    capped_variations,
                    len({url for url in delivered}),
                )
                for index, url in enumerate(delivered):
                    image_metadata = dict(metadata_base)
                    image_metadata["sequence_index"] = index
                    if group_size is not None:
                        image_metadata["group_size"] = group_size
                    generated_images.append(
                        GeneratedImage(
                            url=url,
                            provider=provider.name,
                            prompt=prompt,
                            metadata=image_metadata,
                        )
                    )
            except Exception as exc:  # noqa: BLE001
                logger.warning("生成候选失败(provider=%s): %s", provider.name, exc, extra={"provider": provider.name})
                continue
        else:
            async def _generate_single() -> GeneratedImage:
                request_payload = GenerateRequestPayload(
                    task="image2image",
                    prompt=prompt,
                    provider=provider.name,
                    size=size,
                    params={
                        "reference_images": list(reference_images),
                        "sequential_mode": "auto" if reference_images else "disabled",
                        "num_variations": 1,
                    },
                )
                response = await provider.generate(request_payload)
                urls = _extract_urls(response)
                if not urls:
                    raise RuntimeError(f"{provider.name} 未返回有效图片")
                return GeneratedImage(
                    url=urls[0],
                    provider=provider.name,
                    prompt=prompt,
                    metadata=response.get("metadata", {}),
                )

            tasks = [asyncio.create_task(_generate_single()) for _ in range(num_variations)]
            if capped_variations != num_variations:
                tasks = tasks[:capped_variations]
            images = await asyncio.gather(*tasks, return_exceptions=True)

            for index, item in enumerate(images):
                if isinstance(item, Exception):
                    logger.warning(
                        "生成候选失败(provider=%s): %s",
                        provider.name,
                        item,
                        extra={"provider": provider.name},
                    )
                    continue
                base_metadata = dict(item.metadata or {})
                if group_mode:
                    base_metadata["sequence_index"] = index
                    base_metadata["group_size"] = capped_variations
                generated_images.append(
                    GeneratedImage(
                        url=item.url,
                        provider=item.provider,
                        prompt=item.prompt,
                        metadata=base_metadata,
                    )
                )

        if not generated_images:
            continue

        evaluation = await aggregator.score_candidates(
            task_id=task_id,
            images=generated_images,
            modules=modules,
        )

        verification = await _verify_consistency(
            task_id=task_id,
            reference_images=reference_images,
            generated_images=generated_images,
        )

        provider_summary = []
        for image in generated_images:
            eval_summary = (
                evaluation.image_results.get(image.url)
                if evaluation and evaluation.image_results
                else None
            )
            provider_summary.append(
                {
                    "url": image.url,
                    "sequence_index": image.metadata.get("sequence_index"),
                    "group_size": image.metadata.get("group_size"),
                    "composite_score": getattr(eval_summary, "composite_score", None),
                    "module_scores": getattr(eval_summary, "module_scores", None),
                    "verification": verification.get(image.url),
                }
            )

        _record_pipeline_event(
            "provider_results",
            {
                "task_id": str(task_id),
                "provider": provider.name,
                "sequential": provider.name == "doubao_seedream" and len(generated_images) > 1,
                "requested_variations": num_variations,
                "delivered": len(generated_images),
                "group_mode": group_mode,
                "images": provider_summary,
            },
        )

        for image in generated_images:
            generated.append(
                GeneratedMarketingImage(
                    provider=provider.name,
                    image=image,
                    evaluation=evaluation,
                    verification=verification.get(image.url, {}),
                )
            )

    return generated


async def _verify_consistency(
    *,
    task_id: UUID,
    reference_images: Sequence[str],
    generated_images: Sequence[GeneratedImage],
) -> Dict[str, Dict[str, Any]]:
    """Estimate subject consistency per generated image.

    Uses Doubao vision understanding API when possible; falls back to a
    placeholder score if the call fails. Scores are normalized to [0, 1].
    """
    api_key = (
        os.getenv("ARK_API_KEY")
        or os.getenv("DOUBAO_API_KEY")
        or DEFAULT_ARK_API_KEY
    )

    if not generated_images:
        return {}

    verification: Dict[str, Dict[str, Any]] = {}
    for image in generated_images:
        try:
            score = await _request_consistency_score(
                api_key=api_key,
                reference_images=reference_images,
                candidate_image=image.url,
            )
            verification[image.url] = {
                "status": "scored",
                "score": score,
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Consistency check failed for %s: %s",
                image.url,
                exc,
                extra={"task_id": str(task_id)},
            )
            verification[image.url] = {
                "status": "pending_review",
                "score": 0.0,
                "comment": str(exc),
            }
    return verification


async def _analyze_reference_images(
    *,
    reference_images: Sequence[str],
    platform_hint: Optional[str],
    product_hint: Optional[str],
    style_hint: Optional[str],
) -> Dict[str, Any]:
    """调用豆包视觉理解获取描述，失败则回退到启发式。"""
    api_key = os.getenv("ARK_API_KEY") or os.getenv("DOUBAO_API_KEY") or DEFAULT_ARK_API_KEY
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    model = os.getenv("ARK_ANALYSIS_MODEL", "doubao-seed-1-6-251015")
    prompt_text = _build_analysis_prompt(
        platform_hint=platform_hint,
        product_hint=product_hint,
        style_hint=style_hint,
    )
    contents: List[Dict[str, Any]] = []
    for image in reference_images:
        image_content = _build_chat_image_content(image)
        if image_content:
            contents.append(image_content)
    contents.append(
        {
            "type": "text",
            "text": prompt_text,
        }
    )
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": contents,
            }
        ],
        "max_tokens": 400,
        "temperature": 0.0,
        "top_p": 0.8,
        "stream": False,
        "response_format": {"type": "json_object"},
    }

    try:
        body = await _post_doubao(
            payload=payload,
            headers=headers,
            endpoint="https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        )
        _record_doubao_event("analysis_response", body)
        parsed = _parse_chat_completion(body)
        description = parsed.get("description") or _compose_description(parsed)
        embedding = parsed.get("embedding") or _synthesize_embedding(reference_images)
        return {
            "embedding": embedding,
            "platform": parsed.get("platform") or platform_hint or "淘宝",
            "product": parsed.get("product") or product_hint or "产品",
            "style": parsed.get("style") or style_hint or "质感商业风",
            "keywords": parsed.get("style_keywords", []) or parsed.get("keywords", []),
            "description": description,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("豆包图像理解失败，使用回退逻辑: %s", exc)
        _record_doubao_event("analysis_error", {"error": str(exc)})
        embedding = _synthesize_embedding(reference_images)
        fallback_description_parts = [
            item
            for item in (
                product_hint,
                style_hint,
                platform_hint,
            )
            if isinstance(item, str) and item.strip()
        ]
        fallback_description = "，".join(fallback_description_parts) if fallback_description_parts else None
        return {
            "embedding": embedding,
            "platform": platform_hint or "淘宝",
            "product": product_hint or "产品",
            "style": style_hint or "质感商业风",
            "keywords": [],
            "description": fallback_description,
        }


def _synthesize_embedding(reference_images: Sequence[str], dimension: int = 256) -> Optional[List[float]]:
    if not reference_images:
        return None
    vector = [0.0] * dimension
    for img_index, image in enumerate(reference_images):
        if not isinstance(image, str):
            continue
        digest = hashlib.sha256(image.encode("utf-8", "ignore")).digest()
        for idx, byte in enumerate(digest):
            pos = (idx + img_index * len(digest)) % dimension
            vector[pos] += byte / 255.0
    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 0:
        return vector
    return [value / norm for value in vector]


async def _post_doubao(
    *,
    payload: Dict[str, Any],
    headers: Dict[str, str],
    endpoint: Optional[str] = None,
) -> Dict[str, Any]:
    url = endpoint or os.getenv("ARK_VIDEO_ENDPOINT") or "https://ark.cn-beijing.volces.com/api/v3/videos/understanding"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:  # noqa: PERF203
        body_text = exc.response.text if exc.response is not None else "<empty>"
        logger.warning(
            "Doubao request failed status=%s url=%s body=%s payload=%s",
            exc.response.status_code if exc.response is not None else "unknown",
            exc.request.url if exc.request is not None else url,
            body_text,
            payload,
        )
        raise
    return response.json()


def _build_chat_image_content(source: str) -> Optional[Dict[str, Any]]:
    if not source:
        return None
    if source.startswith("data:"):
        _, _, encoded = source.partition(",")
        if not encoded:
            return None
        return {
            "type": "input_image",
            "image_base64": encoded,
        }
    return {
        "type": "image_url",
        "image_url": {
            "url": source,
        },
    }


def _build_analysis_prompt(
    *,
    platform_hint: Optional[str],
    product_hint: Optional[str],
    style_hint: Optional[str],
) -> str:
    platform_note = platform_hint or "常见电商平台"
    style_note = style_hint or "电商常用布光"
    product_note = product_hint or "产品"
    return (
        "你是电商视觉分析助手，请基于上传的产品图生成简洁的 JSON 输出，严禁输出除 JSON 以外的文字。\n"
        "需要包含字段：\n"
        f'  "product": 主要商品类别，默认"{product_note}"。\n'
        f'  "style": 概述整体风格，如布光/背景/情绪，默认"{style_note}"。\n'
        f'  "style_keywords": 包含 3-5 个场景/光线/材质关键词的数组。\n'
        f'  "platform": 推荐最适合的电商平台，若不确定可返回"{platform_note}"。\n'
        '  "description": 一句话中文语义描述，30 字以内。\n'
        "仅输出 JSON 对象。"
    )


def _build_consistency_prompt(reference_images: Sequence[str], candidate_image: str) -> str:
    count = len(reference_images)
    return (
        "你是电商商品一致性审核助手。请比较候选图片与参考图片的主体是否一致，"
        f"参考图片数量约为 {count}，候选图需保持同类商品、主色调与关键特征。"
        "请输出 JSON，字段：score（0-1 浮点，1 表示完全一致）、comment（中文解释，不超过30字）。"
        "仅返回 JSON。"
    )


def _parse_analysis_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    candidates: List[str] = []
    data = payload.get("data")
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                text = item.get("text") or item.get("result") or item.get("content")
                if text:
                    candidates.append(text)
    elif isinstance(data, dict):
        text = data.get("text") or data.get("result") or data.get("content")
        if text:
            candidates.append(text)

    for text in candidates:
        if not isinstance(text, str):
            continue
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

    return {}


def _compose_description(parsed: Dict[str, Any]) -> Optional[str]:
    product = parsed.get("product")
    style = parsed.get("style")
    keywords = parsed.get("style_keywords") or parsed.get("keywords") or []
    parts = [product if isinstance(product, str) else None, style if isinstance(style, str) else None]
    if isinstance(keywords, list):
        parts.extend([item for item in keywords if isinstance(item, str)])
    parts = [part for part in parts if part]
    if not parts:
        return None
    return "，".join(parts)


def _parse_chat_completion(payload: Dict[str, Any]) -> Dict[str, Any]:
    candidates: List[str] = []
    choices = payload.get("choices")
    if isinstance(choices, list):
        for choice in choices:
            message = choice.get("message") if isinstance(choice, dict) else None
            if not isinstance(message, dict):
                continue
            content = message.get("content")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict):
                        text = part.get("text")
                        if isinstance(text, str):
                            candidates.append(text)
            elif isinstance(content, str):
                candidates.append(content)

    if not candidates:
        # 兼容旧结构，重用之前的解析逻辑
        return _parse_analysis_response(payload)

    for text in candidates:
        if not isinstance(text, str):
            continue
        text = text.strip()
        if not text:
            continue
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    return {}


async def _request_consistency_score(
    *,
    api_key: str,
    reference_images: Sequence[str],
    candidate_image: str,
) -> float:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    base_payload = {
        "model": "doubao-video-understanding",
        "input": {
            "task_type": "image_similarity",
            "reference_images": [_prepare_doubao_image(item, index) for index, item in enumerate(reference_images)],
            "candidate_image": _prepare_doubao_image(candidate_image, 0),
        },
        "response_format": "json",
        "stream": False,
    }

    payload = dict(base_payload)
    payload["parameters"] = {
        "prompt": _build_consistency_prompt(reference_images, candidate_image),
        "max_tokens": 300,
    }

    body = await _post_doubao(payload=payload, headers=headers)
    _record_doubao_event("consistency_response", body)
    score = _extract_consistency_score(body)

    if score is None:
        logger.debug("Consistency score missing, fallback to raw request.")
        fallback_body = await _post_doubao(payload=base_payload, headers=headers)
        _record_doubao_event("consistency_response_fallback", fallback_body)
        score = _extract_consistency_score(fallback_body)

    if score is None:
        raise ValueError(f"未能从豆包响应中提取一致性分数: {body}")
    return max(0.0, min(1.0, score))


def _prepare_doubao_image(source: str, index: int) -> Dict[str, Any]:
    if source.startswith("data:"):
        _, _, encoded = source.partition(",")
        return {
            "type": "base64",
            "name": f"image_{index}",
            "image_base64": encoded,
        }
    return {
        "type": "url",
        "name": f"image_{index}",
        "url": source,
    }


def _extract_consistency_score(payload: Dict[str, Any]) -> Optional[float]:
    seen: set[int] = set()

    def _scan(obj: Any) -> Optional[float]:
        obj_id = id(obj)
        if obj_id in seen:
            return None
        seen.add(obj_id)

        if isinstance(obj, dict):
            for key in ("score", "similarity", "consistency", "consistency_score"):
                if key in obj:
                    value = obj.get(key)
                    try:
                        numeric = float(value)
                        if numeric > 1.0:
                            if numeric <= 100.0:
                                numeric = numeric / 100.0
                            else:
                                numeric = 1.0
                        return numeric
                    except (TypeError, ValueError):
                        continue

            text_value = obj.get("text") or obj.get("content") or obj.get("result")
            if isinstance(text_value, str):
                try:
                    parsed = json.loads(text_value)
                    value = _scan(parsed)
                    if value is not None:
                        return value
                except json.JSONDecodeError:
                    pass

            for nested_key in ("output", "data", "answer", "response", "extra"):
                nested = obj.get(nested_key)
                value = _scan(nested)
                if value is not None:
                    return value

        elif isinstance(obj, list):
            for item in obj:
                value = _scan(item)
                if value is not None:
                    return value
        return None

    return _scan(payload)
    return None


def _extract_urls(response: Dict[str, Any]) -> List[str]:
    urls: List[str] = []
    if isinstance(response.get("images"), list):
        urls.extend([item for item in response["images"] if isinstance(item, str) and item])
    if isinstance(response.get("image_url"), str) and response["image_url"]:
        urls.append(response["image_url"])
    return urls


def _select_best_image(candidates: Sequence[GeneratedMarketingImage]) -> Optional[GeneratedMarketingImage]:
    best: Optional[GeneratedMarketingImage] = None
    best_score = -1.0
    for candidate in candidates:
        evaluation = candidate.evaluation.image_results.get(candidate.image.url) if candidate.evaluation else None
        score = evaluation.composite_score if evaluation else 0.0
        if score > best_score:
            best = candidate
            best_score = score
    return best
