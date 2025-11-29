"""Adapter modules for external and internal generation providers."""

from services.generate.adapters.base import BaseProvider
from services.generate.adapters.dalle import DalleProvider
from services.generate.adapters.nano_banana import NanoBananaProvider
from services.generate.adapters.openrouter import OpenRouterImageProvider
from services.generate.adapters.qwen import QwenProvider
from services.generate.adapters.stable_diffusion import StableDiffusionProvider

__all__ = [
    "BaseProvider",
    "DalleProvider",
    "NanoBananaProvider",
    "OpenRouterImageProvider",
    "StableDiffusionProvider",
]
