import json
import os
from volcenginesdkarkruntime import Ark
from volcenginesdkarkruntime.types.images.images import SequentialImageGenerationOptions

api_key = os.getenv("ARK_API_KEY")
if not api_key:
    raise SystemExit("请先设置 ARK_API_KEY 环境变量")

client = Ark(base_url="https://ark.cn-beijing.volces.com/api/v3", api_key=api_key)

request_kwargs = {
    "model": "doubao-seedream-4-0-250828",
    "prompt": "参考这个LOGO，做一套户外运动品牌视觉设计，品牌名称为GREEN，包括包装袋、帽子、纸盒、手环、挂绳等。绿色视觉主色调，趣味、简约现代风格",
    "image": "https://ark-project.tos-cn-beijing.volces.com/doc_image/seedream4_imageToimages.png",
    "size": "2K",
    "sequential_image_generation": "auto",
    "sequential_image_generation_options": SequentialImageGenerationOptions(max_images=5),
    "response_format": "url",
    "watermark": True,
}

print("=== Request Parameters ===")
print(json.dumps({k: (v.__dict__ if hasattr(v, "__dict__") else v) for k, v in request_kwargs.items()}, ensure_ascii=False, indent=2))

response = client.images.generate(**request_kwargs)
print("=== Response Object ===")

def to_dict(obj):
    if obj is None:
        return None
    if isinstance(obj, (list, tuple, set)):
        return [to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {key: to_dict(value) for key, value in obj.items()}
    if hasattr(obj, "__dict__"):
        return {key: to_dict(value) for key, value in obj.__dict__.items()}
    return obj

raw = to_dict(response)
print(json.dumps(raw, ensure_ascii=False, indent=2))
urls = [item.url for item in getattr(response, "data", [])]
print(f"total={len(urls)} unique={len(set(urls))}")
for idx, url in enumerate(urls, 1):
    print(f"[{idx}] {url}")
