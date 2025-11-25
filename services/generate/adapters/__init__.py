"""Adapter modules for external and internal generation providers."""

from services.generate.adapters.base import BaseProvider
from services.generate.adapters.dalle import DalleProvider
from services.generate.adapters.gemini_2_5 import GeminiFlashProvider
from services.generate.adapters.huggingface import HuggingFaceProvider
from services.generate.adapters.lab_aesthetic_score import (
    LabAestheticScoreProvider,
)
from services.generate.adapters.lab_image_enhance import LabImageEnhanceProvider
from services.generate.adapters.nano_banana import NanoBananaProvider
from services.generate.adapters.qwen import QwenProvider
from services.generate.adapters.stability_free import StabilityFreeProvider
from services.generate.adapters.stable_diffusion import StableDiffusionProvider

__all__ = [
    "BaseProvider",
    "HuggingFaceProvider",
    "StabilityFreeProvider",
    "GeminiFlashProvider",
    "NanoBananaProvider",
    "StableDiffusionProvider",
    "DalleProvider",
    "LabAestheticScoreProvider",
    "LabImageEnhanceProvider",
]
