from __future__ import annotations

from services.generate.adapters.openrouter import OpenRouterImageProvider


class NanoBananaProvider(OpenRouterImageProvider):
    """Nano Banana via OpenRouter."""

    name = "nano_banana"
    model_name = "google/gemini-3-pro-image-preview"
    default_modalities = ["image", "text"]
