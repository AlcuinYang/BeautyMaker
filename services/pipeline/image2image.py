"""图生图营销流程 (一拍即合)

这个流程接收用户提示词、一张或多张参考图片以及一组生成模型。
它会生成候选图片，进行美学评分，并通过豆包视觉理解进行主体一致性检查。
响应格式直接适配前端 UI 的需求。
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import os
import random
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

# 豆包事件日志文件路径
_DOUBAO_LOG_FILE = Path(os.getenv("DOUBAO_LOG_PATH", "logs/doubao_events.jsonl"))
# 流程运行日志文件路径
_PIPELINE_LOG_FILE = Path(os.getenv("PIPELINE_LOG_PATH", "logs/pipeline_runs.jsonl"))
# 默认的 ARK API 密钥
DEFAULT_ARK_API_KEY = os.getenv("DEFAULT_ARK_API_KEY", "")


def _record_doubao_event(event: str, payload: Dict[str, Any]) -> None:
    """记录豆包 API 调用事件到日志文件

    Args:
        event: 事件类型（例如 "analysis_response", "consistency_response"）
        payload: 事件数据负载
    """
    try:
        # 确保日志目录存在
        _DOUBAO_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        # 构建日志记录
        record = {
            "ts": datetime.utcnow().isoformat() + "Z",  # 时间戳
            "event": event,  # 事件类型
            "data": payload,  # 事件数据
        }
        # 追加写入日志文件
        with _DOUBAO_LOG_FILE.open("a", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False)
            handle.write("\n")
    except Exception:  # noqa: BLE001
        logger.debug("Failed to record Doubao event %s", event, exc_info=True)


def _record_pipeline_event(event: str, payload: Dict[str, Any]) -> None:
    """记录流程运行事件到日志文件

    Args:
        event: 事件类型（例如 "pipeline_summary", "provider_results"）
        payload: 事件数据负载
    """
    try:
        # 确保日志目录存在
        _PIPELINE_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        # 构建日志记录
        record = {
            "ts": datetime.utcnow().isoformat() + "Z",  # 时间戳
            "event": event,  # 事件类型
            "data": payload,  # 事件数据
        }
        # 追加写入日志文件
        with _PIPELINE_LOG_FILE.open("a", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False)
            handle.write("\n")
    except Exception:  # noqa: BLE001
        logger.debug("Failed to record pipeline event %s", event, exc_info=True)


# 默认的图像生成提供商列表（默认首选 Seedream）
DEFAULT_PROVIDERS: Sequence[str] = ("doubao_seedream",)
# 默认的评分模块列表
DEFAULT_MODULES = [
    "holistic",        # 整体美学评分
    "color_score",     # 色彩评分
    "contrast_score",  # 对比度评分
    "clarity_eval",    # 清晰度评估
    "noise_eval",      # 噪点评估
    "quality_score",   # 质量评分
]


class Image2ImagePipelineParams(BaseModel):
    """图生图流程的可选参数配置"""
    modules: Optional[List[str]] = None  # 使用的评分模块列表
    image_size: Optional[str] = Field(default=None, pattern=r"^\d+x\d+$")  # 图像尺寸（格式：宽x高）
    num_variations: int = Field(default=1, ge=1, le=15)  # 生成变体的数量（1-15）
    group_mode: bool = False  # 是否启用组模式（仅使用整体评分）
    platform: Optional[str] = None  # 平台提示（例如：淘宝、京东）
    product: Optional[str] = None  # 产品提示
    style: Optional[str] = None  # 风格提示


class Image2ImagePipelineRequest(BaseModel):
    """图生图流程的请求模型"""
    prompt: str  # 用户提示词
    reference_images: List[str] = Field(default_factory=list, min_length=1)  # 参考图片列表（至少1张）
    providers: List[str] = Field(default_factory=list, min_length=1, max_length=4)  # 模型提供商列表（1-4个）
    size: str = Field(default="1024x1024", pattern=r"^\d+x\d+$")  # 生成图像的尺寸
    params: Image2ImagePipelineParams = Field(default_factory=Image2ImagePipelineParams)  # 可选参数

    @model_validator(mode="after")
    def ensure_providers(self) -> "Image2ImagePipelineRequest":
        """验证器：确保至少有一个有效的模型提供商"""
        if not self.providers:
            # 如果没有指定，使用默认的第一个提供商（Seedream）
            self.providers = list(DEFAULT_PROVIDERS[:1])
        # 过滤掉空值
        self.providers = [provider for provider in self.providers if provider]
        if not self.providers:
            raise ValueError("至少需要选择一个模型进行生成。")
        return self


@dataclass
class GeneratedMarketingImage:
    """生成的营销图片数据类"""
    provider: str  # 生成模型的提供商名称
    image: GeneratedImage  # 生成的图片对象
    evaluation: Optional[AggregationResult]  # 美学评分结果
    verification: Dict[str, Any]  # 主体一致性验证结果


async def run_image2image_pipeline(payload: Image2ImagePipelineRequest) -> Dict[str, Any]:
    """编排完整的图生图流程的高级入口函数"""
    # 生成唯一的任务 ID
    task_id = uuid4()
    logger.info("Running image2image pipeline", extra={"task_id": str(task_id)})

    try:
        # 确定使用的评分模块（如果未指定则使用默认模块）
        modules = payload.params.modules or list(DEFAULT_MODULES)
        # 确定图像尺寸（优先使用 params 中的尺寸）
        size = payload.params.image_size or payload.size

        params = payload.params
        # 判断是否为组模式（不再强制压缩模块，保持与文生图一致）
        group_mode = bool(getattr(params, "group_mode", False))

        # 最终的提示词
        final_prompt = payload.prompt

        # 生成所有候选图片
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

        # 检查是否成功生成了候选图片
        if not all_candidates:
            raise RuntimeError("生成阶段未返回任何候选图片")

        def _candidate_score(item: GeneratedMarketingImage) -> float:
            """获取候选图片的综合评分

            Args:
                item: 生成的营销图片对象

            Returns:
                综合评分（0.0-1.0），无评分时返回 0.0
            """
            evaluation_summary = (
                item.evaluation.image_results.get(item.image.url)
                if item.evaluation
                else None
            )
            return float(evaluation_summary.composite_score) if evaluation_summary else 0.0

        # 如果是组模式，按评分排序；否则保持原顺序
        ordered_candidates = (
            sorted(all_candidates, key=_candidate_score, reverse=True)
            if group_mode
            else all_candidates
        )

        # 构建返回给前端的结果列表
        results_payload = []
        for candidate in ordered_candidates:
            # 获取该候选图片的评估摘要
            evaluation_summary = (
                candidate.evaluation.image_results.get(candidate.image.url)
                if candidate.evaluation
                else None
            )
            # 综合评分
            composite = evaluation_summary.composite_score if evaluation_summary else None
        # 各模块的详细评分
            scores: Dict[str, float] = {}
            if evaluation_summary:
                # 返回除整体评分外的所有模块评分
                scores = {
                    key: value
                    for key, value in evaluation_summary.module_scores.items()
                    if key != "holistic"
                }

            # 添加候选图片信息到结果列表
            results_payload.append(
                {
                    "provider": candidate.provider,  # 生成模型
                    "image_url": candidate.image.url,  # 图片 URL
                    "scores": scores,  # 各维度评分
                    "composite_score": composite,  # 综合评分
                    "verification": candidate.verification,  # 一致性验证结果
                    "sequence_index": candidate.image.metadata.get("sequence_index"),  # 序列索引
                    "group_size": candidate.image.metadata.get("group_size"),  # 组大小
                }
            )

        # 选择最佳图片
        best = _select_best_image(all_candidates)
        best_evaluation = (
            best.evaluation.image_results.get(best.image.url)
            if best and best.evaluation
            else None
        )

        # 最佳图片的美学评分（用于前端反馈展示）
        feedback_score = best_evaluation.composite_score if best_evaluation else None

        # 构建成功响应
        response = {
            "status": "success",  # 状态：成功
            "task_id": str(task_id),  # 任务 ID
            "best_image_url": best.image.url if best else None,  # 最佳图片的 URL
            "best_provider": best.provider if best else None,  # 生成最佳图片的模型
            "results": results_payload,  # 所有候选图片的详细信息
            "reference_images": payload.reference_images,  # 用户上传的原始参考图
            "image_size": size,  # 生成的图像尺寸
            "providers_used": sorted({item.provider for item in all_candidates}),  # 使用的所有模型列表
            "final_prompt": final_prompt,  # 最终使用的提示词
            "aesthetic_score": feedback_score,  # 最佳图片的美学评分
            "group_mode": group_mode,  # 是否为组模式
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
    """跨多个模型提供商生成候选图片

    这个函数会：
    1. 为每个提供商生成指定数量的变体图片
    2. 对生成的图片进行美学评分
    3. 验证图片与参考图的主体一致性
    4. 返回所有候选图片及其评估结果

    Args:
        task_id: 任务唯一标识符
        prompt: 用户提示词
        providers: 模型提供商列表
        num_variations: 每个提供商生成的变体数量
        reference_images: 参考图片列表
        modules: 使用的评分模块列表
        size: 生成图像的尺寸
        group_mode: 是否为组模式

    Returns:
        生成的营销图片列表（包含评分和验证结果）
    """
    # 创建评分聚合器实例
    aggregator = ScoringAggregator()
    # 存储所有生成的候选图片
    generated: List[GeneratedMarketingImage] = []

    # 限制变体数量在 1-15 之间
    capped_variations = max(1, min(num_variations, 15))
    # 为每个提供商创建信号量，限制并发请求（每个提供商同时只处理1个请求）
    provider_limits: Dict[str, asyncio.Semaphore] = {
        name: asyncio.Semaphore(1) for name in set(providers)
    }

    async def _run_with_retry(
        *,
        provider_label: str,
        semaphore: asyncio.Semaphore,
        runner,
    ):
        """带重试机制的异步任务执行器

        遇到可重试的错误（如限流、超时）时会自动重试，最多3次。

        Args:
            provider_label: 提供商标签（用于日志）
            semaphore: 信号量（限制并发）
            runner: 要执行的异步函数

        Returns:
            runner 函数的返回值

        Raises:
            Exception: 重试3次后仍失败，或遇到不可重试的错误
        """
        # 重试延迟时间（秒）：第1次重试0.3s，第2次0.8s，第3次1.5s
        delays = [0.3, 0.8, 1.5]
        last_error: Optional[Exception] = None
        for attempt, delay in enumerate(delays, start=1):
            try:
                # 使用信号量限制并发
                async with semaphore:
                    # 添加小的随机延迟，避免请求冲突
                    await asyncio.sleep(0.1 + random.uniform(0, 0.1))
                    return await runner()
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                # 判断是否为可重试的错误（如限流、超时等）
                should_retry = _is_retryable_generation_error(exc)
                if attempt < len(delays) and should_retry:
                    # 计算退避时间（基础延迟 + 随机抖动）
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
                # 不可重试的错误，直接抛出
                raise
        # 所有重试都失败了
        assert last_error  # for type checkers
        raise last_error

    for provider_id in providers:
        provider = get_provider(provider_id)
        semaphore = provider_limits[provider_id]

        generated_images: List[GeneratedImage] = []
        logger.info(
            "Generating with provider=%s references=%s",
            provider.name,
            _summarize_images(reference_images),
        )

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
                async def _execute_seq():
                    response = await provider.generate(request_payload)
                    urls = _extract_urls(response)
                    if not urls:
                        raise RuntimeError(f"{provider.name} 未返回有效图片")
                    return response, urls

                response, urls = await _run_with_retry(
                    provider_label=provider.name,
                    semaphore=semaphore,
                    runner=_execute_seq,
                )
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

                async def _execute_single() -> GeneratedImage:
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

                return await _run_with_retry(
                    provider_label=provider.name,
                    semaphore=semaphore,
                    runner=_execute_single,
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
    """验证生成图片与参考图片的主体一致性

    使用豆包视觉理解 API 来评估每张生成图片与参考图片的主体是否一致。
    如果 API 调用失败，则使用占位符分数（0.0）。
    所有分数归一化到 [0, 1] 区间。

    Args:
        task_id: 任务唯一标识符
        reference_images: 参考图片列表
        generated_images: 生成的图片列表

    Returns:
        字典，键为图片 URL，值为验证结果（包含 status、score、comment）
    """
    # 获取 API 密钥（优先级：ARK_API_KEY > DOUBAO_API_KEY > 默认值）
    api_key = (
        os.getenv("ARK_API_KEY")
        or os.getenv("DOUBAO_API_KEY")
        or DEFAULT_ARK_API_KEY
    )

    # 如果没有生成图片，直接返回空字典
    if not generated_images:
        return {}

    # 存储每张图片的验证结果
    verification: Dict[str, Dict[str, Any]] = {}
    for image in generated_images:
        try:
            # 调用豆包 API 获取一致性分数
            score = await _request_consistency_score(
                api_key=api_key,
                reference_images=reference_images,
                candidate_image=image.url,
            )
            verification[image.url] = {
                "status": "scored",  # 状态：已评分
                "score": score,  # 一致性分数（0.0-1.0）
            }
        except Exception as exc:  # noqa: BLE001
            # 如果验证失败，记录警告并使用占位符分数
            logger.warning(
                "Consistency check failed for %s: %s",
                image.url,
                exc,
                extra={"task_id": str(task_id)},
            )
            verification[image.url] = {
                "status": "pending_review",  # 状态：待人工审核
                "score": 0.0,  # 占位符分数
                "comment": str(exc),  # 错误信息
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
    """基于参考图片 URL 合成一个伪嵌入向量

    这是一个回退方案，当无法从 API 获取真实嵌入时使用。
    通过对图片 URL 进行哈希并转换为归一化向量来生成。

    Args:
        reference_images: 参考图片 URL 列表
        dimension: 嵌入向量的维度（默认 256）

    Returns:
        归一化的嵌入向量（长度为 dimension），如果没有参考图则返回 None
    """
    if not reference_images:
        return None
    # 初始化零向量
    vector = [0.0] * dimension
    # 遍历所有参考图片
    for img_index, image in enumerate(reference_images):
        if not isinstance(image, str):
            continue
        # 对图片 URL 进行 SHA256 哈希
        digest = hashlib.sha256(image.encode("utf-8", "ignore")).digest()
        # 将哈希值的每个字节映射到向量的不同位置
        for idx, byte in enumerate(digest):
            pos = (idx + img_index * len(digest)) % dimension
            vector[pos] += byte / 255.0  # 归一化到 [0, 1]
    # 计算向量的 L2 范数
    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 0:
        return vector
    # 返回归一化后的向量（单位向量）
    return [value / norm for value in vector]


async def _post_doubao(
    *,
    payload: Dict[str, Any],
    headers: Dict[str, str],
    endpoint: Optional[str] = None,
) -> Dict[str, Any]:
    """向豆包 API 发送 POST 请求

    这是一个通用的豆包 API 请求包装器，处理 HTTP 请求和错误。

    Args:
        payload: 请求体（JSON 格式）
        headers: 请求头
        endpoint: API 端点 URL（可选，默认使用环境变量或标准端点）

    Returns:
        API 响应的 JSON 数据

    Raises:
        httpx.HTTPStatusError: HTTP 请求失败时抛出
    """
    # 确定 API 端点（优先级：参数 > 环境变量 > 默认值）
    url = (
        endpoint
        or os.getenv("ARK_CHAT_ENDPOINT")
        or "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    )
    # 创建异步 HTTP 客户端并发送请求（超时 30 秒）
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)
    try:
        # 检查响应状态码，如果不是 2xx 则抛出异常
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:  # noqa: PERF203
        # 记录详细的错误信息（脱敏后的 payload）
        body_text = exc.response.text if exc.response is not None else "<empty>"
        logger.warning(
            "Doubao request failed status=%s url=%s body=%s payload=%s",
            exc.response.status_code if exc.response is not None else "unknown",
            exc.request.url if exc.request is not None else url,
            body_text,
            _redact_payload(payload),  # 脱敏处理（隐藏 base64 图片等敏感信息）
        )
        raise
    return response.json()


def _summarize_image(source: str) -> Dict[str, Any]:
    """生成图片来源的摘要信息（用于日志记录）

    Args:
        source: 图片来源（URL 或 base64 data URI）

    Returns:
        摘要字典：
        - 对于 base64：{"type": "base64", "length": 长度, "preview": 前30字符}
        - 对于 URL：{"type": "url", "value": URL字符串}
    """
    if source.startswith("data:"):
        # 如果是 base64 编码的图片
        _, _, encoded = source.partition(",")
        length = len(encoded)
        preview = encoded[:30] + "..." if length > 30 else encoded
        return {"type": "base64", "length": length, "preview": preview}
    # 如果是普通 URL
    return {"type": "url", "value": source}


def _summarize_images(sources: Sequence[str]) -> List[Dict[str, Any]]:
    """批量生成图片来源的摘要信息

    Args:
        sources: 图片来源列表

    Returns:
        摘要字典列表
    """
    return [_summarize_image(item) for item in sources]


def _redact_payload(obj: Any) -> Any:
    """脱敏处理 API 请求负载（隐藏敏感的 base64 图片数据）

    递归处理字典和列表，将 base64 图片数据替换为占位符。
    这样可以安全地记录日志而不暴露完整的图片数据。

    Args:
        obj: 要脱敏的对象（可以是字典、列表或其他类型）

    Returns:
        脱敏后的对象
    """
    if isinstance(obj, dict):
        redacted: Dict[str, Any] = {}
        for key, value in obj.items():
            if key == "image_base64" and isinstance(value, str):
                # 将 base64 图片数据替换为长度信息
                redacted[key] = f"<base64 length={len(value)}>"
            elif key == "image_url" and isinstance(value, dict):
                # 递归处理嵌套的 image_url 字典
                redacted[key] = _redact_payload(value)
            elif key in {"url"} and isinstance(value, str) and value.startswith("data:"):
                # 将 data URL 替换为占位符
                redacted[key] = "<data-url>"
            else:
                # 递归处理其他字段
                redacted[key] = _redact_payload(value)
        return redacted
    if isinstance(obj, list):
        # 递归处理列表中的每个元素
        return [_redact_payload(item) for item in obj]
    # 其他类型直接返回
    return obj


def _build_chat_image_content(source: str) -> Optional[Dict[str, Any]]:
    """构建豆包聊天 API 的图片内容格式

    将图片来源（URL 或 base64）转换为豆包 API 要求的消息格式。

    Args:
        source: 图片来源（HTTP URL 或 data URI）

    Returns:
        豆包 API 的图片内容字典，如果来源无效则返回 None
    """
    if not source:
        return None
    if source.startswith("data:"):
        # 如果是 base64 编码的图片
        _, _, encoded = source.partition(",")
        if not encoded:
            return None
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{encoded}",
            },
        }
    # 如果是普通 URL
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
    """构建参考图片分析的 prompt

    生成用于豆包视觉理解 API 的 prompt，用于分析参考图片的特征。

    Args:
        platform_hint: 平台提示（如"淘宝"、"京东"）
        product_hint: 产品提示（如"口红"、"手机"）
        style_hint: 风格提示（如"质感商业风"、"小清新"）

    Returns:
        完整的 prompt 字符串
    """
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
    """构建主体一致性检查的 prompt

    生成用于豆包视觉理解 API 的 prompt，用于评估候选图片与参考图片的主体一致性。

    Args:
        reference_images: 参考图片列表
        candidate_image: 候选图片 URL

    Returns:
        完整的 prompt 字符串
    """
    count = len(reference_images)
    return (
        "你是电商商品一致性审核助手。请比较候选图片与参考图片的主体是否一致，"
        f"参考图片数量约为 {count}，候选图需保持同类商品、主色调与关键特征。"
        "图像顺序：前面的图片是参考图，最后一张是候选图。"
        "请输出 JSON，字段：score（0-1 浮点，1 表示完全一致）、comment（中文解释，不超过30字）。"
        "仅返回 JSON。"
    )


def _is_retryable_generation_error(exc: Exception) -> bool:
    """判断生成错误是否可重试

    检查异常信息中是否包含可重试的错误特征（如限流、超时等）。

    Args:
        exc: 捕获的异常对象

    Returns:
        True 如果错误可重试，False 如果不应重试
    """
    message = str(exc).lower()
    # 可重试的错误信号列表
    retry_signals = [
        "throttling",              # 限流
        "rate limit",              # 速率限制
        "ratequota",               # 配额限制
        "too many requests",       # 请求过多
        "timeout",                 # 超时
        "timed out",               # 超时（另一种表述）
        "temporarily unavailable", # 暂时不可用
        "server busy",             # 服务器繁忙
        "429",                     # HTTP 429 状态码
        "connection reset",        # 连接重置
    ]
    return any(signal in message for signal in retry_signals)


def _parse_analysis_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    """解析豆包图像分析响应（旧格式兼容）

    从豆包 API 响应中提取并解析 JSON 结果。
    支持多种响应格式以保证向后兼容。

    Args:
        payload: 豆包 API 返回的原始响应

    Returns:
        解析后的 JSON 字典，失败时返回空字典
    """
    candidates: List[str] = []
    data = payload.get("data")
    # 尝试从 data 字段提取文本
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

    # 尝试解析每个候选文本为 JSON
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
    """将解析结果组合成描述性文本

    从 API 返回的解析结果中提取产品、风格和关键词，组合成中文描述。

    Args:
        parsed: 解析后的字典（包含 product、style、keywords 等字段）

    Returns:
        组合后的中文描述，无内容时返回 None
    """
    product = parsed.get("product")
    style = parsed.get("style")
    keywords = parsed.get("style_keywords") or parsed.get("keywords") or []
    # 收集所有有效的部分
    parts = [product if isinstance(product, str) else None, style if isinstance(style, str) else None]
    if isinstance(keywords, list):
        parts.extend([item for item in keywords if isinstance(item, str)])
    # 过滤掉 None 值
    parts = [part for part in parts if part]
    if not parts:
        return None
    # 用逗号连接各部分
    return "，".join(parts)


def _parse_chat_completion(payload: Dict[str, Any]) -> Dict[str, Any]:
    """解析豆包聊天完成响应（新格式）

    从豆包 Chat Completion API 响应中提取并解析 JSON 结果。
    这是较新的响应格式，通过 choices[].message.content 访问。

    Args:
        payload: 豆包 API 返回的原始响应

    Returns:
        解析后的 JSON 字典，失败时返回空字典
    """
    candidates: List[str] = []
    choices = payload.get("choices")
    # 从 choices 中提取所有文本内容
    if isinstance(choices, list):
        for choice in choices:
            message = choice.get("message") if isinstance(choice, dict) else None
            if not isinstance(message, dict):
                continue
            content = message.get("content")
            # content 可能是列表或字符串
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict):
                        text = part.get("text")
                        if isinstance(text, str):
                            candidates.append(text)
            elif isinstance(content, str):
                candidates.append(content)

    if not candidates:
        # 如果新格式没有找到内容，尝试旧格式（向后兼容）
        return _parse_analysis_response(payload)

    # 尝试解析每个候选文本为 JSON
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
    """请求豆包 API 评估候选图片与参考图片的一致性

    构建包含参考图和候选图的视觉理解请求，让豆包评估主体一致性。

    Args:
        api_key: 豆包 API 密钥
        reference_images: 参考图片列表
        candidate_image: 候选图片 URL

    Returns:
        一致性分数（0.0-1.0）

    Raises:
        ValueError: 如果无法从响应中提取分数
    """
    # 构建请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    # 确定使用的模型（优先级：一致性模型 > 分析模型 > 默认模型）
    model = (
        os.getenv("ARK_CONSISTENCY_MODEL")
        or os.getenv("ARK_ANALYSIS_MODEL")
        or "doubao-seed-1-6-251015"
    )

    # 构建消息内容：先添加所有参考图片，再添加候选图片，最后添加 prompt
    contents: List[Dict[str, Any]] = []
    for image in reference_images:
        chat_image = _build_chat_image_content(image)
        if chat_image:
            contents.append(chat_image)

    candidate_chat_image = _build_chat_image_content(candidate_image)
    if candidate_chat_image:
        contents.append(candidate_chat_image)

    # 添加文本 prompt
    contents.append(
        {
            "type": "text",
            "text": _build_consistency_prompt(reference_images, candidate_image),
        }
    )

    # 构建 API 请求负载
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": contents,
            }
        ],
        "max_tokens": 300,  # 限制响应长度
        "temperature": 0.0,  # 使用确定性输出
        "top_p": 0.8,
        "stream": False,
        "response_format": {"type": "json_object"},  # 要求返回 JSON
    }

    # 发送请求到豆包 API
    body = await _post_doubao(
        payload=payload,
        headers=headers,
        endpoint="https://ark.cn-beijing.volces.com/api/v3/chat/completions",
    )
    # 记录响应到日志
    _record_doubao_event("consistency_response", body)
    # 从响应中提取分数
    score = _extract_consistency_score(body)

    if score is None:
        raise ValueError(f"未能从豆包响应中提取一致性分数: {body}")
    # 确保分数在 [0, 1] 范围内
    score = max(0.0, min(1.0, score))
    # 记录调试信息
    _record_doubao_event(
        "consistency_debug",
        {
            "model": model,
            "reference_images": _summarize_images(reference_images),
            "candidate_image": _summarize_image(candidate_image),
            "score": score,
        },
    )
    return score


def _prepare_doubao_image(source: str, index: int) -> Dict[str, Any]:
    """准备豆包 API 的图片输入格式（旧格式，已废弃）

    Args:
        source: 图片来源（URL 或 base64 data URI）
        index: 图片索引

    Returns:
        豆包 API 的图片输入字典
    """
    if source.startswith("data:"):
        # base64 格式
        _, _, encoded = source.partition(",")
        return {
            "type": "base64",
            "name": f"image_{index}",
            "image_base64": encoded,
        }
    # URL 格式
    return {
        "type": "url",
        "name": f"image_{index}",
        "url": source,
    }


def _extract_consistency_score(payload: Dict[str, Any]) -> Optional[float]:
    """从豆包 API 响应中递归提取一致性分数

    这个函数会递归搜索响应中所有可能包含分数的字段。
    支持多种字段名和嵌套结构，以适应不同的响应格式。

    Args:
        payload: 豆包 API 返回的原始响应

    Returns:
        提取出的一致性分数（0.0-1.0），失败时返回 None
    """
    # 记录已访问的对象 ID，防止循环引用导致无限递归
    seen: set[int] = set()

    def _scan(obj: Any) -> Optional[float]:
        """递归扫描对象以查找分数字段"""
        obj_id = id(obj)
        if obj_id in seen:
            # 已经访问过这个对象，避免循环
            return None
        seen.add(obj_id)

        if isinstance(obj, dict):
            # 尝试直接从已知的分数字段获取值
            for key in ("score", "similarity", "consistency", "consistency_score"):
                if key in obj:
                    value = obj.get(key)
                    try:
                        numeric = float(value)
                        # 如果分数大于1，可能是百分制，需要归一化
                        if numeric > 1.0:
                            if numeric <= 100.0:
                                numeric = numeric / 100.0
                            else:
                                # 超过100的值视为异常，限制为1.0
                                numeric = 1.0
                        return numeric
                    except (TypeError, ValueError):
                        continue

            # 尝试从文本字段中解析 JSON
            text_value = obj.get("text") or obj.get("content") or obj.get("result")
            if isinstance(text_value, str):
                try:
                    parsed = json.loads(text_value)
                    value = _scan(parsed)
                    if value is not None:
                        return value
                except json.JSONDecodeError:
                    pass

            # 递归搜索嵌套字段
            for nested_key in ("output", "data", "answer", "response", "extra"):
                nested = obj.get(nested_key)
                value = _scan(nested)
                if value is not None:
                    return value

        elif isinstance(obj, list):
            # 递归搜索列表中的每个元素
            for item in obj:
                value = _scan(item)
                if value is not None:
                    return value
        return None

    return _scan(payload)


def _extract_urls(response: Dict[str, Any]) -> List[str]:
    """从生成响应中提取图片 URL

    支持两种格式：
    - images: 图片 URL 数组
    - image_url: 单个图片 URL

    Args:
        response: 模型提供商的生成响应

    Returns:
        提取出的图片 URL 列表
    """
    urls: List[str] = []
    # 提取数组格式的图片 URL
    if isinstance(response.get("images"), list):
        urls.extend([item for item in response["images"] if isinstance(item, str) and item])
    # 提取单个图片 URL
    if isinstance(response.get("image_url"), str) and response["image_url"]:
        urls.append(response["image_url"])
    return urls


def _select_best_image(candidates: Sequence[GeneratedMarketingImage]) -> Optional[GeneratedMarketingImage]:
    """从候选图片中选择综合评分最高的图片

    Args:
        candidates: 候选图片列表

    Returns:
        评分最高的图片，如果列表为空则返回 None
    """
    best: Optional[GeneratedMarketingImage] = None
    best_score = -1.0
    # 遍历所有候选图片，找出评分最高的
    for candidate in candidates:
        evaluation = candidate.evaluation.image_results.get(candidate.image.url) if candidate.evaluation else None
        score = evaluation.composite_score if evaluation else 0.0
        if score > best_score:
            best = candidate
            best_score = score
    return best
