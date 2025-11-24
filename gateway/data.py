"""静态 Mock 数据，供前端原型调试使用。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

APPLICATIONS: List[Dict[str, Any]] = [
    {
        "id": "text2image",
        "slug": "qwen-text2image",
        "title": "最美图片",
        "author": "Aesthetic Lab",
        "cover": "/covers/text2image.png",
        "desc": "输入文字，生成高质量图像。",
        "tags": ["生成", "文生图", "AI绘画"],
        "likes": 720,
        "views": 3400,
        "category": "image",
        "modules": [
            "color_score",
            "contrast_score",
            "clarity_eval",
            "noise_eval",
        ],
    },
    {
        "id": "image-compose",
        "slug": "image-compose-seedream",
        "title": "一拍即合",
        "author": "Aesthetic Lab",
        "cover": "/covers/image-compose.png",
        "desc": "上传产品照片，一键生成电商宣传图。",
        "tags": ["图生图", "营销", "智能生成"],
        "likes": 512,
        "views": 2210,
        "category": "image",
        "modules": [
            "holistic",
            "color_score",
            "contrast_score",
            "clarity_eval",
        ],
    },
    # {
    #     "id": "image2video",
    #     "slug": "image-to-video-alpha",
    #     "title": "图生视频 · Motion",
    #     "author": "Aesthetic Lab",
    #     "cover": "/covers/image2video.png",
    #     "desc": "从静态图像生成动效视频。",
    #     "tags": ["视频生成", "动态图像"],
    #     "likes": 412,
    #     "views": 2103,
    #     "category": "video",
    #     "modules": ["clarity_eval", "quality_score"],
    # },
    # {
    #     "id": "style-transfer",
    #     "slug": "style-transfer-lite",
    #     "title": "风格迁移 · Lite",
    #     "author": "Aesthetic Lab",
    #     "cover": "/covers/style-transfer.png",
    #     "desc": "一键将作品转换为不同艺术流派风格。",
    #     "tags": ["风格转换", "图像处理"],
    #     "likes": 188,
    #     "views": 983,
    #     "category": "style",
    #     "modules": ["color_score", "quality_score"],
    # },
    {
        "id": "aesthetic-workspace",
        "slug": "aesthetic-workspace",
        "title": "Aesthetic Workspace",
        "author": "Aesthetic Lab",
        "cover": "/covers/aesthetic-workspace.png",
        "desc": "人物模特生成与美学作品展示的一体化创作台。",
        "tags": ["人物模特", "美学图库", "灵感"],
        "likes": 628,
        "views": 3190,
        "category": "image",
        "modules": [
            "holistic",
            "quality_score",
        ],
    },
]

APP_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "text2image": {
        "id": "text2image",
        "name": "Qwen 文生图",
        "description": "多轮迭代的高质量文本生成图像引擎。",
        "default_params": {
            "prompt": "清晨薄雾中的未来感城市，一束阳光穿透玻璃穹顶",
            "size": "1024x1024",
            "num_outputs": 1,
            "style": "cinematic",
            "guidance_scale": 7.5,
        },
        "module_options": [
            {
                "key": "color_score",
                "label": "色彩美学",
                "description": "衡量色彩平衡与和谐度。",
            },
            {
                "key": "contrast_score",
                "label": "对比度",
                "description": "检测光影层次，提升画面层次感。",
            },
            {
                "key": "clarity_eval",
                "label": "清晰度评估",
                "description": "关注细节锐度与噪点抑制。",
            },
            {
                "key": "noise_eval",
                "label": "噪声评估",
                "description": "评估画面纯净度与噪声水平。",
            },
        ],
        "param_schema": [
            {
                "key": "prompt",
                "type": "textarea",
                "label": "提示词",
                "placeholder": "描述你想要的画面...",
            },
            {
                "key": "style",
                "type": "select",
                "label": "画面风格",
                "options": [
                    {"label": "电影感", "value": "cinematic"},
                    {"label": "赛博朋克", "value": "cyberpunk"},
                    {"label": "现代插画", "value": "illustration"},
                ],
            },
            {
                "key": "num_outputs",
                "type": "slider",
                "label": "输出张数",
                "min": 1,
                "max": 4,
            },
            {
                "key": "size",
                "type": "select",
                "label": "分辨率",
                "options": [
                    {"label": "768×768", "value": "768x768"},
                    {"label": "1024×1024", "value": "1024x1024"},
                    {"label": "1280×720", "value": "1280x720"},
                ],
            },
            {
                "key": "enable_aesthetic",
                "type": "toggle",
                "label": "启用美学增强",
                "default": True,
            },
        ],
    },
    "image2video": {
        "id": "image2video",
        "name": "Motion 图生视频",
        "description": "将静态画面转换为连贯动效。",
        "default_params": {
            "duration": 8,
            "motion_intensity": 0.6,
            "fps": 24,
            "prompt": "将赛博城市夜景照片化为动态霓虹雨景",
        },
        "module_options": [
            {
                "key": "clarity_eval",
                "label": "清晰度评估",
                "description": "确保动效过程中保持画面细节。",
            },
            {
                "key": "quality_score",
                "label": "整体质量",
                "description": "综合衡量影片流畅度与完成度。",
            },
        ],
        "param_schema": [
            {
                "key": "reference_image",
                "type": "image_upload",
                "label": "参考图片",
            },
            {
                "key": "duration",
                "type": "slider",
                "label": "视频时长(秒)",
                "min": 4,
                "max": 12,
            },
            {
                "key": "motion_intensity",
                "type": "slider",
                "label": "动效强度",
                "min": 0.1,
                "max": 1.0,
                "step": 0.1,
            },
        ],
    },
    "style-transfer": {
        "id": "style-transfer",
        "name": "风格迁移 Lite",
        "description": "将上传的图片转换为目标艺术风格。",
        "default_params": {
            "style": "van_gogh",
            "strength": 0.65,
            "prompt": "以梵高星空风格重绘山城夜景",
        },
        "module_options": [
            {
                "key": "color_score",
                "label": "色彩美学",
                "description": "保持色彩统一与风格一致性。",
            },
            {
                "key": "quality_score",
                "label": "整体质量",
                "description": "衡量迁移后作品的完整度。",
            },
        ],
        "param_schema": [
            {
                "key": "reference_image",
                "type": "image_upload",
                "label": "原图上传",
            },
            {
                "key": "style",
                "type": "select",
                "label": "目标风格",
                "options": [
                    {"label": "梵高", "value": "van_gogh"},
                    {"label": "浮世绘", "value": "ukiyo_e"},
                    {"label": "中国水墨", "value": "ink"},
                ],
            },
            {
                "key": "strength",
                "type": "slider",
                "label": "风格强度",
                "min": 0.2,
                "max": 1.0,
                "step": 0.05,
            },
        ],
    },
    "image-compose": {
        "id": "image-compose",
        "name": "一拍即合 · 图生图",
        "description": "上传产品照片，自动生成多风格电商宣传图。",
        "default_params": {
            "templates": ["clean", "fresh", "trend"],
            "providers": ["qwen", "doubao_seedream"],
        },
        "module_options": [
            {
                "key": "holistic",
                "label": "整体美学",
                "description": "综合衡量营销图的视觉吸引力。",
            },
            {
                "key": "color_score",
                "label": "色彩表现",
                "description": "检查色彩是否鲜明统一。",
            },
            {
                "key": "clarity_eval",
                "label": "主体清晰",
                "description": "确保商品主体清晰可见。",
            },
        ],
        "param_schema": [
            {
                "key": "reference_images",
                "type": "image_upload",
                "label": "产品图片",
            },
            {
                "key": "templates",
                "type": "select",
                "label": "模板风格",
                "options": [
                    {"label": "简洁干净", "value": "clean"},
                    {"label": "清新活力", "value": "fresh"},
                    {"label": "潮流社交", "value": "trend"},
                ],
            },
        ],
    },
}

WORKS: List[Dict[str, Any]] = [
    {
        "id": "work-0001",
        "thumbnail": "https://cdn.example.com/works/work-0001.png",
        "title": "晨雾中的玻璃穹顶城市",
        "score": 0.91,
        "module_summary": {
            "color_score": 0.88,
            "contrast_score": 0.79,
            "clarity_eval": 0.93,
        },
        "app_id": "text2image",
        "author": {
            "id": "user-01",
            "name": "Nova",
            "avatar": "https://cdn.example.com/avatars/nova.png",
        },
        "created_at": datetime.now().isoformat(),
    },
    {
        "id": "work-0002",
        "thumbnail": "https://cdn.example.com/works/work-0002.gif",
        "title": "霓虹雨夜街景动画",
        "score": 0.84,
        "module_summary": {
            "quality_score": 0.86,
            "clarity_eval": 0.8,
        },
        "app_id": "image2video",
        "author": {
            "id": "user-02",
            "name": "Kite",
            "avatar": "https://cdn.example.com/avatars/kite.png",
        },
        "created_at": datetime.now().isoformat(),
    },
]

USER_PROFILES: Dict[str, Dict[str, Any]] = {
    "user-01": {
        "id": "user-01",
        "name": "Nova",
        "avatar": "https://cdn.example.com/avatars/nova.png",
        "bio": "跨媒体视觉设计师，热爱生成式艺术。",
        "credits": 82,
        "membership": "pro",
        "recent_apps": ["text2image", "style-transfer"],
    },
}

GALLERY_ITEMS: List[Dict[str, Any]] = [
    {
        "id": "gallery-001",
        "title": "晨光中的竹林仙子",
        "image_url": "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=900&q=80",
        "likes": 428,
        "comments": 32,
        "author": "Nova",
        "tags": ["portrait", "fantasy", "emerald"],
        "created_at": datetime.now().isoformat(),
    },
    {
        "id": "gallery-002",
        "title": "赛博和风街角",
        "image_url": "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?auto=format&fit=crop&w=900&q=80",
        "likes": 389,
        "comments": 18,
        "author": "Kite",
        "tags": ["street", "cyberpunk", "night"],
        "created_at": datetime.now().isoformat(),
    },
    {
        "id": "gallery-003",
        "title": "星海的听风者",
        "image_url": "https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e?auto=format&fit=crop&w=900&q=80",
        "likes": 512,
        "comments": 46,
        "author": "Muse",
        "tags": ["space", "portrait", "dream"],
        "created_at": datetime.now().isoformat(),
    },
    {
        "id": "gallery-004",
        "title": "风中的现代舞",
        "image_url": "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?auto=format&fit=crop&w=900&q=80",
        "likes": 274,
        "comments": 11,
        "author": "Nova",
        "tags": ["motion", "dance", "vogue"],
        "created_at": datetime.now().isoformat(),
    },
    {
        "id": "gallery-005",
        "title": "琥珀城市的夜",
        "image_url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=900&q=80",
        "likes": 301,
        "comments": 21,
        "author": "Atlas",
        "tags": ["city", "amber", "noir"],
        "created_at": datetime.now().isoformat(),
    },
]
