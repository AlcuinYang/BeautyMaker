"""静态 Provider 元数据，供 /api/providers 返回使用。"""

PROVIDER_META = {
    "qwen": {
        "display_name": "Tongyi Qianwen (Qwen)",
        "description": "Qwen-Image: complex text rendering, ideal for posters and text-heavy images.",
        "category": "image_generation",
        "is_free": False,
        "icon": "/icons/qwen.svg",
        "endpoint": "https://dashscope.aliyuncs.com",
    },
    "wan": {
        "display_name": "Tongyi Wanxiang (Wan)",
        "description": "Wanxiang: general image generation with reference image support.",
        "category": "image_generation",
        "is_free": False,
        "icon": "/icons/wan.svg",
        "endpoint": "https://dashscope.aliyuncs.com",
    },
    "dalle": {
        "display_name": "OpenAI DALL-E (OpenRouter)",
        "description": "DALL-E 3 via OpenRouter with proxy routing.",
        "category": "image_generation",
        "is_free": False,
        "icon": "/icons/dalle.svg",
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
    },
    "nano_banana": {
        "display_name": "Nano Banana (OpenRouter)",
        "description": "High-fidelity image editing via OpenRouter proxy.",
        "category": "image_generation",
        "is_free": False,
        "icon": "/icons/nano-banana.svg",
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
    },
    "stable_diffusion": {
        "display_name": "Stable Diffusion",
        "description": "Open-source image generation model.",
        "category": "image_generation",
        "is_free": False,
        "icon": "/icons/sd.svg",
        "endpoint": None,
    },
}
