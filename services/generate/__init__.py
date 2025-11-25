"""Generation provider registry."""

from services.generate.adapters.dalle import DalleProvider
from services.generate.adapters.doubao_seedream import DoubaoSeedreamProvider
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

_REGISTRY = {
    QwenProvider.name: QwenProvider(),
    HuggingFaceProvider.name: HuggingFaceProvider(),
    StabilityFreeProvider.name: StabilityFreeProvider(),
    GeminiFlashProvider.name: GeminiFlashProvider(),
    NanoBananaProvider.name: NanoBananaProvider(),
    StableDiffusionProvider.name: StableDiffusionProvider(),
    DalleProvider.name: DalleProvider(),
    LabAestheticScoreProvider.name: LabAestheticScoreProvider(),
    LabImageEnhanceProvider.name: LabImageEnhanceProvider(),
    DoubaoSeedreamProvider.name: DoubaoSeedreamProvider(),
}


def get_provider(name: str):
    provider = _REGISTRY.get(name)
    if provider is None:
        raise ValueError(f"Unknown provider: {name}")
    return provider


def list_providers() -> list[str]:
    return list(_REGISTRY.keys())
