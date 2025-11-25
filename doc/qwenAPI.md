# 通义万相 - 文生图 V2 API 参考（精简整理版）

**文档同步时间：2025-10-28**
基于阿里云 Model Studio 的文本生成图像（Text-to-Image）服务。

---

# 1. 概述

通义万相文生图 API 支持从文本生成图片，包含多种风格与摄影效果。
当前 API 为 **异步接口**，完整流程包括：

1. **创建任务 → 获取 task_id**
2. **轮询任务 → 获取生成图像 URL**

任务通常需 **1–2 分钟**（受排队影响）。

---

# 2. 模型列表与能力限制

| 模型名称                       | 简介                             | 分辨率与格式                                    |
| -------------------------- | ------------------------------ | ----------------------------------------- |
| **wan2.5-t2i-preview（推荐）** | 取消单边限制；仅受总像素面积约束，可生成如 768×2700 | 总像素范围：768×768 ～ 1440×1440；宽高比 1:4–4:1；png |
| **wan2.2-t2i-flash（推荐）**   | 2.2 极速版，速度较 2.1 快 50%          | 宽高：512–1440；png                           |
| **wan2.2-t2i-plus（推荐）**    | 2.2 专业版，稳定性提升                  | png                                       |
| wanx2.1-t2i-turbo          | 2.1 极速版                        | —                                         |
| wanx2.1-t2i-plus           | 2.1 专业版                        | —                                         |
| wanx2.0-t2i-turbo          | 2.0 极速版                        | —                                         |

> 注意：北京与新加坡地域 API Key 与 Base URL 不可混用。

---

# 3. API Endpoint

### 创建任务（POST）

* 新加坡：
  `https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis`
* 北京：
  `https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis`

### 查询任务（GET）

* 新加坡：
  `https://dashscope-intl.aliyuncs.com/api/v1/tasks/{task_id}`
* 北京：
  `https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}`

---

# 4. Headers

| Header                            | 是否必需 | 含义               |
| --------------------------------- | ---- | ---------------- |
| `Content-Type: application/json`  | 必选   | 请求格式             |
| `Authorization: Bearer <API_KEY>` | 必选   | API Key 鉴权       |
| `X-DashScope-Async: enable`       | 必选   | 必须设置，否则报错不支持同步调用 |

---

# 5. 请求体说明（Request Body）

```json
{
  "model": "wan2.5-t2i-preview",
  "input": {
    "prompt": "一间有着精致窗户的花店，漂亮的木质门，摆放着花朵"
  },
  "parameters": {
    "size": "1024*1024",
    "n": 1
  }
}
```

---

## 5.1 字段详解

### model（必选）

模型名称，例如：

* `wan2.5-t2i-preview`
* `wan2.2-t2i-flash`

---

## 5.2 input（必选）

| 字段                  | 必选 | 说明                                     |
| ------------------- | -- | -------------------------------------- |
| **prompt**          | 是  | 中英文均可。2.5 最大 2000 字符；2.2 及以下最大 800 字符。 |
| **negative_prompt** | 否  | 不希望画面出现的内容，如“人物”。支持≤500字符。             |

示例（带反向提示词）：

```json
"input": {
  "prompt": "雪地，白色小教堂，极光，冬日场景，柔和的光线。",
  "negative_prompt": "人物"
}
```

---

## 5.3 parameters（可选）

| 字段                | 类型     | 说明                                      |
| ----------------- | ------ | --------------------------------------- |
| **size**          | string | 格式：`宽*高`。不同模型有不同限制（见模型列表）。              |
| **n**             | int    | 1–4 张，默认 4。直接影响费用。建议测试用 1。              |
| **prompt_extend** | bool   | 是否开启智能提示词扩写。2.5 默认 false；2.2 以下默认 true。 |
| **watermark**     | bool   | 是否添加水印（右下角 “AI生成”）。                     |
| **seed**          | int    | 0–2147483647。用于结果可控性。n>1 时自动 seed+1 递增。 |

---

# 6. 响应示例（创建任务）

成功：

```json
{
  "output": {
    "task_status": "PENDING",
    "task_id": "0385dc79-5ff8-4d82-bcb6-xxxxxx"
  },
  "request_id": "4909100c-7b5a-9f92-bfe5-xxxxxx"
}
```

失败（示例）：

```json
{
  "code":"InvalidApiKey",
  "message":"Invalid API-key provided.",
  "request_id":"fb53c4ec-1c12-4fc4-a580-xxxxxx"
}
```

---

# 7. 轮询任务结果（GET）

建议轮询间隔：**10 秒**
任务状态流转：

```
PENDING → RUNNING → (SUCCEEDED / FAILED)
```

成功后返回图像 URL（有效期 24h，请尽快下载到 OSS 或本地）。

---

# 8. 图像 URL 使用说明

* 链接有效期：24 小时
* 获取后应立即下载并转存
* 推荐使用阿里云 OSS 作为持久化存储

---

# 9. 常见分辨率推荐

| 比例   | 分辨率（示例）             |
| ---- | ------------------- |
| 1:1  | 1280×1280、1024×1024 |
| 2:3  | 800×1200            |
| 3:2  | 1200×800            |
| 3:4  | 960×1280            |
| 4:3  | 1280×960            |
| 9:16 | 720×1280            |
| 16:9 | 1280×720            |
| 21:9 | 1344×576            |

---

# 10. Task 响应字段说明

| 字段                 | 含义                                                          |
| ------------------ | ----------------------------------------------------------- |
| `task_id`          | 创建任务时生成，24h 有效                                              |
| `task_status`      | PENDING / RUNNING / SUCCEEDED / FAILED / CANCELED / UNKNOWN |
| `request_id`       | 用于日志排查                                                      |
| `code` / `message` | 错误信息（仅失败时返回）                                                |

---

# 11. 错误排查

常见报错：

* **缺少 X-DashScope-Async** → current user api does not support synchronous calls
* API Key 地域混用 → InvalidApiKey
* 分辨率超限 → 参数校验错误

详见官方错误码文档。

---

# 12. 示例：完整调用流程 (curl)

### Step 1: 创建任务

```bash
curl -X POST https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis \
-H 'X-DashScope-Async: enable' \
-H "Authorization: Bearer $DASHSCOPE_API_KEY" \
-H 'Content-Type: application/json' \
-d '{
    "model": "wan2.5-t2i-preview",
    "input": { "prompt": "花店，木门，精致窗户，摆放着花朵" },
    "parameters": { "size": "1024*1024", "n": 1 }
}'
```

### Step 2: 查询任务结果

```bash
curl -X GET https://dashscope-intl.aliyuncs.com/api/v1/tasks/<task_id> \
-H "Authorization: Bearer $DASHSCOPE_API_KEY"
```

---

# 13. 注意事项

* 不同地域 **API Key 不通用**
* 建议使用 **固定 seed** 来改善可控性
* prompt_extend 会增加延迟
* n 越大费用越高，测试阶段务必用 1

---

# 14. 参考链接

* API Key 获取
* 模型列表与价格
* 文生图 Prompt 指南
* OSS 持久化存储

