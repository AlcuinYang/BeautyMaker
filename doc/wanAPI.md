# 通义千问 - 文生图（Qwen-Image）API 参考（精简整理版）

**文档更新时间：2025-11-12**
模型支持复杂文本渲染、多行布局、段落级文本生成和精细细节刻画，适合通用海报、卡通风格、图文混排等生成需求。

---

# 1. 概述

通义千问 Qwen-Image 支持通过 **同步 HTTP 接口** 直接返回生成图像，无需异步轮询。

核心特性：

* 多模态图像生成
* 复杂文本布局（段落、标题、气泡等）
* 更强的细节渲染能力
* 提供 prompt 改写、反向提示词、水印控制等参数

---

# 2. API Endpoint（同步接口）

### 新加坡地域（推荐）

```
POST https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation
```

### 北京地域

```
POST https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation
```

> 注意：地域与 API Key **严格绑定**，不得跨地域混用。

---

# 3. Headers

| Header                            | 必选 | 说明                     |
| --------------------------------- | -- | ---------------------- |
| `Content-Type: application/json`  | 是  | 必须为 `application/json` |
| `Authorization: Bearer <API_KEY>` | 是  | 使用百炼 API Key 鉴权        |

---

# 4. 请求体结构（Request Body）

```json
{
  "model": "qwen-image-plus",
  "input": {
    "messages": [
      {
        "role": "user",
        "content": [
          { "text": "一只坐着的橘黄色的猫，表情愉悦，活泼可爱，逼真准确。" }
        ]
      }
    ]
  },
  "parameters": {
    "negative_prompt": "",
    "prompt_extend": true,
    "watermark": false,
    "size": "1328*1328"
  }
}
```

---

# 5. 字段说明

## 5.1 model（必选）

模型名称：

| 模型                      | 说明                      |
| ----------------------- | ----------------------- |
| **qwen-image-plus（推荐）** | 与 qwen-image 能力一致，但价格更低 |
| qwen-image              | 通用图像生成模型                |

---

## 5.2 input（必选）

| 字段           | 类型     | 说明                   |
| ------------ | ------ | -------------------- |
| **messages** | array  | 单轮对话，仅允许一个元素         |
| role         | string | 必须为 `user`           |
| content      | array  | 内容数组，当前仅支持 `text`    |
| text         | string | 正向提示词（≤800 字符），支持中英文 |

提示词应描述你期望的内容、风格、布局。例如：

```
Healing-style poster of puppies playing ball on grass, cute and warm atmosphere...
```

错误示例：

* content 传多个 text → 报错
* 未传 text → 报错

---

## 5.3 parameters（可选）

| 字段                  | 类型      | 说明                               |
| ------------------- | ------- | -------------------------------- |
| **negative_prompt** | string  | 反向提示词（≤500 字符）                   |
| **size**            | string  | 输出分辨率，如 `1328*1328`              |
| **n**               | integer | 固定为 **1**，否则报错                   |
| **prompt_extend**   | bool    | 是否开启智能 prompt 改写（默认 `true`）      |
| **watermark**       | bool    | 是否添加 “Qwen-Image” 水印（默认 `false`） |
| **seed**            | int     | [0, 2147483647]，固定随机性            |

默认分辨率与比例：

| 分辨率           | 比例   |
| ------------- | ---- |
| 1664*928      | 16:9 |
| 1472*1140     | 4:3  |
| 1328*1328（默认） | 1:1  |
| 1140*1472     | 3:4  |
| 928*1664      | 9:16 |

---

# 6. 请求示例（curl）

```bash
curl --location 'https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation' \
--header 'Content-Type: application/json' \
--header "Authorization: Bearer $DASHSCOPE_API_KEY" \
--data '{
    "model": "qwen-image-plus",
    "input": {
      "messages": [
        {
          "role": "user",
          "content": [
            {
              "text": "Healing-style hand-drawn poster featuring three puppies playing with a ball..."
            }
          ]
        }
      ]
    },
    "parameters": {
      "negative_prompt": "",
      "prompt_extend": true,
      "watermark": false,
      "size": "1328*1328"
    }
}'
```

---

# 7. 响应结构（Response）

成功示例：

```json
{
  "output": {
    "choices": [
      {
        "finish_reason": "stop",
        "message": {
          "role": "assistant",
          "content": [
            {
              "image": "https://dashscope-result-sz.oss-cn-shenzhen.aliyuncs.com/xxx.png?Expires=xxx"
            }
          ]
        }
      }
    ],
    "task_metric": {
      "TOTAL": 1,
      "FAILED": 0,
      "SUCCEEDED": 1
    }
  },
  "usage": {
    "width": 1328,
    "image_count": 1,
    "height": 1328
  },
  "request_id": "xxx"
}
```

失败示例：

```json
{
  "request_id": "xxx",
  "code": "InvalidParameter",
  "message": "num_images_per_prompt must be 1"
}
```

---

# 8. 字段说明（Output）

## output.choices

| 字段            | 含义                  |
| ------------- | ------------------- |
| image         | 生成图 URL（PNG，24h 有效） |
| finish_reason | stop 表示正常结束         |
| role          | assistant           |

## usage

| 字段             | 含义      |
| -------------- | ------- |
| image_count    | 当前固定 1  |
| width / height | 输出图像分辨率 |

## 任务有效期

* 图像 URL 有效期 **24 小时**
* 必须及时下载并保存

---

# 9. 常见错误与排查

| 错误码              | 原因                    |
| ---------------- | --------------------- |
| InvalidApiKey    | API Key 地域不匹配 / Key 错 |
| InvalidParameter | n ≠ 1、text 缺失、尺寸非法    |
| MissingParameter | 未传必选字段                |
| BadRequest       | JSON 结构不合法            |

更多请参考官方错误码文档。

---

# 10. SDK 调用示例（Python）

```python
import os
import dashscope
from dashscope import MultiModalConversation

dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'

messages = [
    {
        "role": "user",
        "content": [{"text": "一只橘猫，表情愉悦，坐在草地上"}]
    }
]

resp = MultiModalConversation.call(
    model="qwen-image-plus",
    messages=messages,
    size="1328*1328"
)

print(resp)
```

---

# 11. 注意事项

* 单次请求只能包含 **一个 messages 元素**
* content 仅支持 **一个 text 字段**
* n 参数被强制固定为 1
* 水印默认关闭，可开启
* 图像 URL 24h 失效，必须及时保存
* prompt_extend 会增加 3–4 秒延迟

---

