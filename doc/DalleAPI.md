# OpenAI GPT-Image-1 API Handbook

# OpenAI 图像生成（GPT-Image-1）开发者手册

**Full Bilingual Version｜完整中英双语版**
**Source: [https://platform.openai.com/docs/guides/image-generation](https://platform.openai.com/docs/guides/image-generation)**

---

# 0. Overview 总览

GPT-Image-1 是 OpenAI 最新、最先进的图像生成模型，支持从文本生成图片、编辑图片、多轮对话修改、局部编辑、参考图生成、透明背景、流式生成等。

This document provides a **fully-structured, bilingual, developer-oriented** reference extracted strictly from the official documentation.

---

# 1. Two APIs for Image Generation

# 图像生成的两种 API 方式

OpenAI 提供两套接口：

## 1.1 Image API (simplest)

## Image API（最简单的方式）

能力：

* Generate images from text prompt 从零生成图
* Edit existing images 编辑图像（含 mask）
* Create variations（仅 DALL·E 2）

使用模型：

* gpt-image-1
* DALL·E 2 / DALL·E 3

适用场景：
**单次生成/编辑，不需要多轮迭代。**

---

## 1.2 Responses API (multi-turn, conversational)

## Responses API（多轮对话式图像生成）

能力：

* Multi-turn editing 多轮编辑
* Tools system 工具系统接入 image_generation
* Mix text + image inputs（file IDs 或 base64）混合输入
* Streaming 流式生成
* 高保真编辑（input_fidelity）

仅支持 gpt-image-1。

适用场景：
**复杂交互、多轮优化、逐步进化图像的应用。**

---

# 2. Choose the Right API

# 如何选择 API？

| 场景                            | 推荐 API          |
| ----------------------------- | --------------- |
| 只生成一次图片                       | Image API       |
| 对图像迭代修改（prompt 或 reference 图） | Responses API   |
| 希望高度可控、可追踪编辑链路                | Responses API   |
| 优先低延迟                         | Image API（JPEG） |

---

# 3. Supported Models

# 支持的模型

| Model 模型    | Capability 能力                    |
| ----------- | -------------------------------- |
| GPT-Image-1 | 最新、最强、指令追随好、文本渲染强、支持 edit/mask   |
| DALL·E 3    | 高质量生成（仅生成）                       |
| DALL·E 2    | Edit + Inpaint + Variations，成本最低 |

官方建议：**优先使用 GPT-Image-1**

---

# 4. Image API

# 图像 API

Endpoint:

```
POST https://api.openai.com/v1/images/generations
POST https://api.openai.com/v1/images/edits
POST https://api.openai.com/v1/images/variations (DALL·E 2)
```

Headers:

```
Authorization: Bearer $OPENAI_API_KEY
Content-Type: application/json
```

---

## 4.1 Generate Images

## 生成图像

### Request (Node.js)

```javascript
const result = await openai.images.generate({
  model: "gpt-image-1",
  prompt: "A children's book drawing of a vet checking a baby otter",
});
const image = result.data[0].b64_json;
```

### Request (Python)

```python
result = client.images.generate(
    model="gpt-image-1",
    prompt="A children's book drawing..."
)
img_bytes = base64.b64decode(result.data[0].b64_json)
```

---

## 4.2 Edit Images

## 编辑图像

支持：

* base image 单张或多张输入图
* mask（局部编辑）
* 高输入保真（input_fidelity）

### Example

```python
result = client.images.edit(
    model="gpt-image-1",
    image=[open("a.png","rb"), open("b.png","rb")],
    prompt="Combine these into a gift basket"
)
```

---

## 4.3 Edit with Mask（inpainting）

## 使用 Mask 局部编辑

* 必须 PNG 并带 alpha channel
* mask 与原图尺寸一致
* GPT-Image-1 为 prompt-based inpainting（不是像素精确填补）

```python
result = client.images.edit(
  model="gpt-image-1",
  image=open("sunlit_lounge.png","rb"),
  mask=open("mask.png","rb"),
  prompt="Replace area with a flamingo"
)
```

---

# 5. Responses API

# 多轮对话式 Responses API

Endpoint:

```
POST https://api.openai.com/v1/responses
```

核心结构：

```json
{
  "model": "gpt-5",
  "input": "Generate an image...",
  "tools": [
    { "type": "image_generation" }
  ]
}
```

提取图片：

```python
image_data = [
  o.result for o in response.output 
  if o.type == "image_generation_call"
]
```

---

## 5.1 Multi-Turn Editing

## 多轮图像生成/编辑

两种方式：

### A. previous_response_id

引用前一步的 image_generation_call

### B. 使用 image_generation_call 的 id

显式将前一次生成的 image 作为输入

---

## 5.2 Multi-Turn Example

```python
response = client.responses.create(
  model="gpt-5",
  input="Generate a cat hugging an otter",
  tools=[{"type":"image_generation"}]
)

follow = client.responses.create(
  model="gpt-5",
  previous_response_id=response.id,
  input="Make it realistic",
  tools=[{"type":"image_generation"}]
)
```

---

# 6. Streaming Image Generation

# 图像流式生成（Partial Images）

支持参数：
`partial_images: 0~3`

作用：生成过程中产出渐进版本（progressive）。

```python
stream = client.images.generate(
    model="gpt-image-1",
    prompt="river of owl feathers",
    stream=True,
    partial_images=2
)
```

每个 partial 会产生成本（+100 image tokens）。

---

# 7. Input Fidelity

# 输入图高保真模式

`input_fidelity = "low" | "high"`

高保真用于：

* 保留 logo
* 保留脸部
* 高细节纹理传递

成本更高（更多 image tokens）。

Example:

```python
tools=[{
  "type":"image_generation",
  "input_fidelity":"high"
}]
```

---

# 8. Customize Image Output

# 自定义图片输出

## 8.1 Size（not flexible like SD）

尺寸有限制：

* 1024×1024（默认）
* 1536×1024（横向）
* 1024×1536（竖向）
* auto

## 8.2 Quality

* low
* medium
* high
* auto（默认）

## 8.3 Format

* png（默认）
* jpeg（更快）
* webp

## 8.4 Compression（JPEG/WebP）

`output_compression: 0 ~ 100`

## 8.5 Transparent Background

透明背景：

```
background: "transparent"
```

仅支持：

* PNG
* WebP

---

# 9. Prompt Revision

# Prompt 自动改写

Responses API 中，GPT-4.1 / GPT-5 会自动 rewrite prompt。

可从 image_generation_call.revised_prompt 获取。

示例：

```json
{
  "revised_prompt": "A gray tabby cat hugging an otter wearing an orange scarf..."
}
```

---

# 10. Mask Requirements

# Mask 要求

* 与原图尺寸一致
* 必须 PNG
* 必须带 alpha channel
* 黑白 mask 需程序添加 alpha 通道（页面原文已示例）

---

# 11. Cost & Latency

# 成本与延迟计算

图像成本 =
**输入文本 tokens**

* **输入图像 tokens（编辑时）**
* **输出图像 tokens（与质量和尺寸成比例）**

成本例（GPT-Image-1）：

| Quality | 1024×1024  | 1024×1536 | 1536×1024 |
| ------- | ---------- | --------- | --------- |
| Low     | 272 tokens | 408       | 400       |
| Medium  | 1056       | 1584      | 1568      |
| High    | 4160       | 6240      | 6208      |

Partial image：+100 tokens each.

---

# 12. Limitations

# 模型限制

* Latency：复杂 prompt 可达 120 秒
* Text rendering：比 DALL·E 强，但仍非完美
* Consistency：角色一致性仍有限
* Composition control：对布局敏感任务仍有偏差

---

# 13. Content Moderation

# 内容审核

参数：

```
moderation: "auto" (default) | "low"
```

**Note:** “low” 仅降低程度，不禁用审核。

---

# 14. Example Summary

# 关键示例速览

## 14.1 Generate

```python
client.images.generate(model="gpt-image-1", prompt="...")
```

## 14.2 Edit

```python
client.images.edit(model="gpt-image-1", image=[...], prompt="...")
```

## 14.3 Mask Inpaint

```python
client.images.edit(model="gpt-image-1", image=img, mask=mask, prompt="...")
```

## 14.4 Responses Multi-Turn

```python
client.responses.create(
  model="gpt-5",
  input="...",
  previous_response_id=...
)
```

## 14.5 Transparent Background

```python
background="transparent"
```

## 14.6 High Fidelity

```python
input_fidelity="high"
```

---

# END

# 完整文档结束
