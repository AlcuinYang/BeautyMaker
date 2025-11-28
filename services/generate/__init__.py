"""Generation provider registry."""

from services.generate.adapters.doubao_seedream import DoubaoSeedreamProvider
from services.generate.adapters.nano_banana import NanoBananaProvider
from services.generate.adapters.qwen import QwenProvider
from services.generate.adapters.wan import WanProvider
from services.generate.adapters.stable_diffusion import StableDiffusionProvider

_REGISTRY = {
    QwenProvider.name: QwenProvider(),
    WanProvider.name: WanProvider(),
    NanoBananaProvider.name: NanoBananaProvider(),
    StableDiffusionProvider.name: StableDiffusionProvider(),
    DoubaoSeedreamProvider.name: DoubaoSeedreamProvider(),
}


def get_provider(name: str):
    provider = _REGISTRY.get(name)
    if provider is None:
        raise ValueError(f"Unknown provider: {name}")
    return provider


def list_providers() -> list[str]:
    return list(_REGISTRY.keys())
