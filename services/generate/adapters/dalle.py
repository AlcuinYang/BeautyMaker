from __future__ import annotations

from services.generate.adapters.openrouter import OpenRouterImageProvider


class DalleProvider(OpenRouterImageProvider):
    """OpenRouter proxied DALL·E provider."""

    name = "dalle"
    model_name = "openai/gpt-5-image"
    default_modalities = ["text", "image"]
