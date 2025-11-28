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
    "nano_banana": {
        "display_name": "Nano Banana (Fal.ai)",
        "description": "High-fidelity image editing & generation.",
        "category": "image_generation",
        "is_free": False,
        "icon": "/icons/nano-banana.svg",
        "endpoint": "https://fal.run/fal-ai/nano-banana",
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
