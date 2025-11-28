"""Aesthetic reviewer service for generating image reviews.

This module provides the AestheticReviewer class which generates:
- Single image critiques highlighting strengths and commercial value
- Comparative reviews explaining why the best image was selected over lower-scoring images
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from services.common.models import ComparativeReview, GeneratedImage
from services.scoring.aggregator import ImageEvaluation
from services.scoring.holistic.doubao_client import DoubaoAestheticClient

logger = logging.getLogger(__name__)


class AestheticReviewer:
    """Service for generating reviews for candidate images.

    This service uses the DoubaoAestheticClient to generate:
    - Single image critiques focusing on strengths, improvements, and commercial value
    - Comparative reviews comparing the best-scoring image with the lowest-scoring image,
      explaining the differences in AIGC quality metrics
    """
    def __init__(self, client: Optional[DoubaoAestheticClient] = None) -> None:
        """Initialize the reviewer with a Doubao aesthetic client."""
        self._doubao_client = client or DoubaoAestheticClient()

    async def review_candidates(
        self,
        candidates: List[GeneratedImage],
        evaluations: Dict[str, ImageEvaluation],
        context: str = "general",
    ) -> Optional[ComparativeReview]:
        """Generate a review for the candidate images.

        For single images, generates a critique highlighting strengths and areas for improvement.
        For multiple images, generates a comparative review explaining why the best image won.

        Args:
            candidates: List of generated images to review
            evaluations: Dictionary mapping image URLs to their evaluation results
            context: Review context - "general" for artistic critique or "ecommerce" for commercial analysis

        Returns:
            A ComparativeReview object if successful, None if unable to generate
            (e.g., no candidates, missing evaluations, API failure)
        """
        if not candidates:
            logger.debug("No candidates to review")
            return None

        if not evaluations:
            logger.debug("No evaluations available for review")
            return None

        # Handle single image critique
        if len(candidates) == 1:
            return await self._review_single_image(candidates[0], evaluations, context)

        # Need at least 2 candidates for comparative review
        if len(candidates) < 2:
            logger.debug("Not enough candidates for comparative review (need >= 2, got %d)", len(candidates))
            return None

        # Sort candidates by composite score (highest to lowest)
        scored_candidates = []
        for candidate in candidates:
            evaluation = evaluations.get(candidate.url)
            if evaluation and evaluation.composite_score is not None:
                scored_candidates.append((candidate, evaluation))

        if len(scored_candidates) < 2:
            logger.debug("Not enough scored candidates for comparative review")
            return None

        # Sort by composite score descending
        scored_candidates.sort(key=lambda x: x[1].composite_score, reverse=True)

        # Best (highest score) and Loser (lowest score)
        best_image, best_eval = scored_candidates[0]
        loser_image, loser_eval = scored_candidates[-1]

        # Find candidate indices for labeling
        best_idx = next((idx for idx, img in enumerate(candidates) if img.url == best_image.url), -1)
        loser_idx = next((idx for idx, img in enumerate(candidates) if img.url == loser_image.url), -1)

        best_label = f"候选{best_idx + 1}" if best_idx >= 0 else "候选A"
        loser_label = f"候选{loser_idx + 1}" if loser_idx >= 0 else "候选B"

        # Build the prompt
        prompt = self._build_prompt(
            best_label=best_label,
            best_eval=best_eval,
            loser_label=loser_label,
            loser_eval=loser_eval,
            context=context,
        )

        try:
            # Call Doubao to compare the images
            result = await self._doubao_client.compare_images(
                image_urls=[best_image.url, loser_image.url],
                prompt=prompt,
            )

            if not result:
                logger.warning("Doubao compare_images returned empty result")
                return None

            # Parse the result into a ComparativeReview
            review = ComparativeReview(
                title=result.get("title", "精选佳作"),
                analysis=result.get("analysis", "经过多维度评估，这张图片在综合表现上最优。"),
                key_difference=result.get("key_difference", "综合美感"),
            )

            logger.info("Generated comparative review: %s", review.model_dump())
            return review

        except Exception as exc:
            logger.warning("Failed to generate comparative review: %s", exc)
            return None

    async def _review_single_image(
        self,
        image: GeneratedImage,
        evaluations: Dict[str, ImageEvaluation],
        context: str = "general",
    ) -> Optional[ComparativeReview]:
        """Generate a critique for a single image.

        Args:
            image: The generated image to review
            evaluations: Dictionary mapping image URLs to their evaluation results
            context: Review context - "general" or "ecommerce"

        Returns:
            A ComparativeReview object with critique if successful, None otherwise
        """
        evaluation = evaluations.get(image.url)
        if not evaluation or evaluation.composite_score is None:
            logger.debug("No evaluation found for single image review")
            return None

        # Build the single image analysis prompt
        prompt = self._build_single_image_prompt(evaluation, context)

        try:
            # Call Doubao to analyze the single image
            result = await self._doubao_client.compare_images(
                image_urls=[image.url],
                prompt=prompt,
            )

            if not result:
                logger.warning("Doubao single image analysis returned empty result")
                return None

            # Parse the result into a ComparativeReview
            review = ComparativeReview(
                title=result.get("title", "图片亮点"),
                analysis=result.get("analysis", "图片整体表现良好，具备一定的商业价值。"),
                key_difference=result.get("key_difference", "核心优势"),
            )

            logger.info("Generated single image critique: %s", review.model_dump())
            return review

        except Exception as exc:
            logger.warning("Failed to generate single image critique: %s", exc)
            return None

    def _build_single_image_prompt(self, evaluation: ImageEvaluation, context: str = "general") -> str:
        """Build the AIGC-native prompt for single image analysis.

        Args:
            evaluation: Evaluation results for the image
            context: Review context - "general" or "ecommerce"

        Returns:
            A formatted prompt string for the Doubao API
        """
        def fmt(score: Optional[float]) -> str:
            """Format score to 1 decimal place on 0-10 scale."""
            return f"{(score or 0) * 10:.1f}"

        if context == "ecommerce":
            return self._build_ecommerce_single_prompt(evaluation, fmt)
        return self._build_general_single_prompt(evaluation, fmt)

    def _build_general_single_prompt(
        self, evaluation: ImageEvaluation, fmt: callable
    ) -> str:
        """Build general artistic critique prompt for single image."""
        prompt = f"""
请作为 AIGC 质量质检专家，对这张生成图片进行专业点评：

【图片评分】
- 综合评分：{fmt(evaluation.composite_score)}/10
- 结构合理性(手/脸)：{fmt(evaluation.module_scores.get('clarity_eval'))}/10
- 语义忠实度：{fmt(evaluation.module_scores.get('quality_score'))}/10
- 物理逻辑(光影/透视)：{fmt(evaluation.module_scores.get('contrast_score'))}/10
- 画面纯净度：{fmt(evaluation.module_scores.get('noise_eval'))}/10

【任务要求】
请根据上述评分，生成一段约 100 字的【专业点评】。
1. **亮点分析**：指出图片在哪些维度表现优秀（如：结构完整、光影自然、语义准确）。
2. **潜在不足**：如果存在评分较低的维度，简要说明可能的改进方向（如：略有瑕疵、可优化空间）。
3. **商业价值**：一句话总结该图片的实用性和推荐度。

【输出格式】
严格 JSON：
{{
    "title": "亮点：[4-8字短标题]",
    "analysis": "[专业点评内容]",
    "key_difference": "[1-2个核心优势关键词]"
}}
"""
        return prompt

    def _build_ecommerce_single_prompt(
        self, evaluation: ImageEvaluation, fmt: callable
    ) -> str:
        """Build ecommerce-focused critique prompt for single product image."""
        prompt = f"""
你是资深电商视觉总监。请评估这张商品生成图的商业价值。

【评分数据】
- 综合评分：{fmt(evaluation.composite_score)}/10
- 结构合理性(主体完整性)：{fmt(evaluation.module_scores.get('clarity_eval'))}/10
- 语义忠实度(产品还原度)：{fmt(evaluation.module_scores.get('quality_score'))}/10
- 物理逻辑(光影/布光)：{fmt(evaluation.module_scores.get('contrast_score'))}/10
- 画面纯净度(背景干净度)：{fmt(evaluation.module_scores.get('noise_eval'))}/10

【核心关注点】
1. **主体完整性**：产品是否变形？边缘是否清晰？Logo 或文字是否清晰可辨？（这是死线，变形即不合格）
2. **背景干扰**：背景是否喧宾夺主？是否有杂乱元素干扰视线？背景是否干净统一？
3. **光影质感**：是否有高级的商业布光感？产品反光、阴影是否自然？是否提升了产品档次？

【任务要求】
请生成约 50 字的商业点评。
1. 直接指出优点（如：瓶身反光自然，背景纯净不抢镜）。
2. 明确指出缺点（如：边缘有轻微噪点，产品底部略有变形）。
3. 给出一句话的商业推荐度（如：适合电商主图使用 / 需优化后再上架）。

【输出格式】
严格 JSON：
{{
    "title": "[4-8字商业评价，如'产品主体突出'、'光影质感高级'、'背景略显杂乱']",
    "analysis": "[约50字点评，聚焦产品完整性、背景、光影]",
    "key_difference": "[核心优势关键词，如'光影高级'、'主体清晰'、'背景纯净']"
}}
"""
        return prompt

    def _build_prompt(
        self,
        *,
        best_label: str,
        best_eval: ImageEvaluation,
        loser_label: str,
        loser_eval: ImageEvaluation,
        context: str = "general",
    ) -> str:
        """Build the AIGC-native prompt for comparative review.

        Args:
            best_label: Label for the best image (e.g., "候选1")
            best_eval: Evaluation results for the best image
            loser_label: Label for the loser image (e.g., "候选2")
            loser_eval: Evaluation results for the loser image
            context: Review context - "general" or "ecommerce"

        Returns:
            A formatted prompt string for the Doubao API
        """
        def fmt(score: Optional[float]) -> str:
            """Format score to 1 decimal place on 0-10 scale."""
            return f"{(score or 0) * 10:.1f}"

        if context == "ecommerce":
            return self._build_ecommerce_comparison_prompt(
                best_label, best_eval, loser_label, loser_eval, fmt
            )
        return self._build_general_comparison_prompt(
            best_label, best_eval, loser_label, loser_eval, fmt
        )

    def _build_general_comparison_prompt(
        self,
        best_label: str,
        best_eval: ImageEvaluation,
        loser_label: str,
        loser_eval: ImageEvaluation,
        fmt: callable,
    ) -> str:
        """Build general artistic comparison prompt."""
        # Use AIGC-Native labels mapped to internal keys
        prompt = f"""
请作为 AIGC 质量质检专家，对比分析以下两张生成图片:

【{best_label}（优胜图）】
- 综合评分：{fmt(best_eval.composite_score)}/10
- 结构合理性(手/脸)：{fmt(best_eval.module_scores.get('clarity_eval'))}/10
- 语义忠实度：{fmt(best_eval.module_scores.get('quality_score'))}/10
- 物理逻辑(光影/透视)：{fmt(best_eval.module_scores.get('contrast_score'))}/10
- 画面纯净度：{fmt(best_eval.module_scores.get('noise_eval'))}/10

【{loser_label}（参照图）】
- 综合评分：{fmt(loser_eval.composite_score)}/10
- 结构合理性(手/脸)：{fmt(loser_eval.module_scores.get('clarity_eval'))}/10
- 语义忠实度：{fmt(loser_eval.module_scores.get('quality_score'))}/10
- 物理逻辑(光影/透视)：{fmt(loser_eval.module_scores.get('contrast_score'))}/10
- 画面纯净度：{fmt(loser_eval.module_scores.get('noise_eval'))}/10

【任务要求】
请根据上述评分差异，生成一段约 100 字的【对比点评】。
1. **归因分析**：直接指出图片 A 在哪些维度胜出。**重点关注结构合理性**（如：优胜图手指结构完整，而参照图出现了肢体扭曲）。
2. **缺陷指出**：明确指出图片 B 的主要 AIGC 瑕疵（如：伪影、逻辑错误、语义缺失）。
3. **总结**：一句话总结 A 的获胜理由。

【输出格式】
严格 JSON：
{{
    "title": "胜出理由：[4-8字短标题]",
    "analysis": "[对比分析内容]",
    "key_difference": "[1-2个核心差异点关键词]"
}}
"""
        return prompt

    def _build_ecommerce_comparison_prompt(
        self,
        best_label: str,
        best_eval: ImageEvaluation,
        loser_label: str,
        loser_eval: ImageEvaluation,
        fmt: callable,
    ) -> str:
        """Build ecommerce-focused comparison prompt for product images."""
        prompt = f"""
你是资深电商视觉总监。请对比以下两张商品生成图，分析优胜图为何更适合带货。

【{best_label}（优胜图）】
- 综合评分：{fmt(best_eval.composite_score)}/10
- 结构合理性(主体完整性)：{fmt(best_eval.module_scores.get('clarity_eval'))}/10
- 语义忠实度(产品还原度)：{fmt(best_eval.module_scores.get('quality_score'))}/10
- 物理逻辑(光影/布光)：{fmt(best_eval.module_scores.get('contrast_score'))}/10
- 画面纯净度(背景干净度)：{fmt(best_eval.module_scores.get('noise_eval'))}/10

【{loser_label}（参照图）】
- 综合评分：{fmt(loser_eval.composite_score)}/10
- 结构合理性(主体完整性)：{fmt(loser_eval.module_scores.get('clarity_eval'))}/10
- 语义忠实度(产品还原度)：{fmt(loser_eval.module_scores.get('quality_score'))}/10
- 物理逻辑(光影/布光)：{fmt(loser_eval.module_scores.get('contrast_score'))}/10
- 画面纯净度(背景干净度)：{fmt(loser_eval.module_scores.get('noise_eval'))}/10

【任务要求】
对比分析两张商品图，生成约 80 字的电商视觉对比点评。
1. **主体对比**：优胜图的产品是否更清晰？是否更完整无变形？Logo/文字是否更清晰？
   例：「优胜图瓶身边缘清晰锐利，而参照图瓶口有轻微扭曲。」
2. **背景对比**：优胜图的背景是否更干净？是否更突出产品？
   例：「优胜图背景纯净统一，参照图背景元素略显杂乱。」
3. **光影对比**：优胜图的商业布光是否更高级？产品质感是否更好？
   例：「优胜图反光自然高级，参照图光影略显平淡。」
4. **商业结论**：一句话总结优胜图为何更适合电商主图使用。

【输出格式】
严格 JSON：
{{
    "title": "胜出理由：[4-8字商业评价，如'产品更清晰'、'背景更纯净'、'光影更高级']",
    "analysis": "[约80字对比点评，聚焦产品完整性、背景、光影三大维度]",
    "key_difference": "[核心差异关键词，如'主体更清晰'、'背景更干净'、'布光高级']"
}}
"""
        return prompt
