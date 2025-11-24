from pathlib import Path
from typing import Dict


BASE_DIR = Path(__file__).resolve().parent.parent


def get_provider_endpoints() -> Dict[str, str]:
    """Map provider identifiers to their base URLs."""
    return {
        "openai": "https://api.openai.com/v1/images",
        "banana": "https://banana.dev/api",
        "stability": "https://api.stability.ai/v1",
    }


FUSION_WEIGHTS = {
    # 颜色美学权重
    "color_score": 0.2,
    # 对比度权重
    "contrast_score": 0.2,
    # 清晰度权重
    "clarity_eval": 0.2,
    # 噪声评估权重（更低更好）
    "noise_eval": 0.1,
    # 整体质量权重
    "quality_score": 0.3,
}


class Settings:
    """Runtime configuration."""

    app_env: str = "development"
    provider_timeouts: float = 30.0


settings = Settings()
