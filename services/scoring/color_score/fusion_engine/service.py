from __future__ import annotations

from typing import Dict

from config.default import FUSION_WEIGHTS


class FusionEngine:
    """融合引擎，按权重计算综合美学分数。"""

    def compute(self, module_scores: Dict[str, float]) -> float:
        if not module_scores:
            return 0.0

        primary = module_scores.get("color_score")
        if primary is not None:
            try:
                return round(float(primary), 3)
            except (TypeError, ValueError):
                pass

        total_weight = 0.0
        weighted_sum = 0.0

        for module, score in module_scores.items():
            if score is None:
                continue
            weight = FUSION_WEIGHTS.get(module, 1.0)
            weighted_sum += score * weight
            total_weight += weight

        if total_weight == 0.0:
            return 0.0

        return round(weighted_sum / total_weight, 3)
