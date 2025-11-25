# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

AestheticsEngine（美学引擎）是一个模块化的 AI 美学评估和图像生成引擎。集成了 13+ 个图像生成提供商（OpenAI DALL·E、通义千问、豆包 Seedream、Gemini 等），并使用豆包 Vision 模型进行多维度美学评分。

**技术栈：**
- 后端：FastAPI + Python 3.10+（异步编程，httpx）
- 前端：React 19 + TypeScript + Vite + Tailwind CSS
- AI 集成：豆包 Vision 进行 5 维美学评分 + 中文点评

## 开发命令

### 后端

```bash
# 安装依赖（需要 Python 3.10+）
pip install -e .[dev]

# 启动开发服务器
uvicorn gateway.main:app --reload --host 0.0.0.0 --port 8000

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_pipeline_endpoint.py -v

# 运行单个测试
pytest tests/test_pipeline_endpoint.py::test_text2image_pipeline -v
```

### 前端

```bash
cd frontend

# 安装依赖（需要 Node.js 20.19+）
npm install

# 启动开发服务器（默认 http://localhost:5173）
npm run dev

# 连接远程后端
VITE_AE_API="http://your-host:8000" npm run dev

# 构建生产版本
npm run build

# 代码检查
npm run lint
```

### 必需的环境变量

```bash
# 图像生成提供商
export DASHSCOPE_API_KEY="sk-xxxxx"              # 通义千问（阿里云 DashScope）
export ARK_API_KEY="Bearer xxxxx"                # 豆包 Seedream & Vision
export OPENAI_API_KEY="sk-xxxxx"                 # DALL·E

# 豆包美学评分配置
export HOLISTIC_MODEL="doubao-seed-1-6-vision"
export HOLISTIC_PROMPT="prompts/doubao_aesthetic.prompt"

# 可选配置
export GLOBAL_HTTP_PROXY="http://proxy:port"
export VITE_AE_API="http://127.0.0.1:8000"       # 前端 API 地址
```

## 架构概览

### 服务编排模式

系统采用 **4 层编排架构**：

```
Gateway 层 (gateway/main.py)
    ↓
Orchestrator 层 (gateway/orchestrator.py)
    ↓
Service 层 (services/)
    ├── Generation Service → 13 个提供商适配器
    ├── Scoring Aggregator → 豆包 Vision + 技术评分模块
    ├── Enhancement Service（预留超分辨率等功能）
    └── Selector Service（最佳候选选择）
```

**关键流程：** 请求 → Gateway → Orchestrator → [生成 + 评分 + 增强 + 选优] → 响应

### 核心架构概念

#### 1. 提供商适配器模式

所有图像生成提供商都实现 `BaseProvider` 接口（`services/generate/adapters/base.py`）：

```python
class BaseProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def generate(self, request: GenerateRequestPayload) -> Dict[str, Any]: ...
```

**提供商注册表：** `services/generate/__init__.py` 维护 `_PROVIDERS` 字典。添加新提供商的步骤：
1. 在 `services/generate/adapters/your_provider.py` 创建适配器
2. 在 `services/generate/__init__.py` 注册
3. 在 `services/generate/routes/provider_info.py` 添加元数据

#### 2. 豆包 Vision 优先评分系统

`ScoringAggregator`（`services/scoring/aggregator.py`）实现了**优先-降级策略**：

1. **优先：** 调用豆包 Vision API（`services/scoring/holistic/doubao_client.py`）
   - 返回 5 个美学维度 + 1 个综合分（1-10 分制）
   - 包含每个维度的中文点评（≤50 字）
   - 维度映射关系：`composition → contrast_score`、`light_color → color_score` 等

2. **降级：** 如果豆包失败，使用技术评分模块（MNet 等）

**维度映射（关键）：**
```python
{
    "composition": "contrast_score",        # 构图
    "light_color": "color_score",           # 光影色彩
    "style_coherence": "noise_eval",        # 风格一致性
    "emotional_impact": "quality_score",    # 情感表达
    "clarity_integrity": "clarity_eval",    # 清晰完整度
    "final_score": "holistic"               # 综合美感
}
```

**分数归一化：** 豆包返回 1-10 分；系统内部归一化为 0-1；前端显示为 1-10 分。

#### 3. 两条管线架构

**文生图管线**（`services/pipeline/text2image.py`）：
```
用户 Prompt → [可选扩写] → 多提供商并行生成
→ 豆包评分 → 选择最佳 → 返回 {最佳图, 所有候选, 摘要}
```

**图生图管线**（`services/pipeline/image2image.py`）：
```
参考图 + Prompt → 豆包分析（产品/风格/关键词）
→ [可选 Prompt 库融合] → 多提供商生成
→ 豆包美学评分 → 一致性检测（参考图 vs 生成图）
→ 选择最佳 → 更新模板权重 → 事件日志
```

**一致性检测：** 使用豆包 Vision 比较参考图与生成图，返回一致性分数（0-1）和评语。

#### 4. 事件日志系统

两个 JSONL 日志文件追踪执行过程：
- `logs/doubao_events.jsonl`：所有豆包 API 调用（分析、评分、一致性）
- `logs/pipeline_runs.jsonl`：管线执行摘要

格式：`{"ts": "ISO-8601", "event": "事件类型", "data": {...}}`

### 代码规范（来自 CONTRIBUTING.md）

**适配器结构：** 将负载构建、提交、结果提取分离到独立函数。

**日志记录：**
- 使用模块级日志：`logger = logging.getLogger(__name__)`
- 包含关键字段：mode/model/size/task_id
- **永远不要记录 API 密钥或敏感信息** - 在日志中屏蔽它们

**类型注解：**
- 所有请求/响应使用 Pydantic 模型
- 为函数参数、返回值和重要局部变量添加类型
- 使用 `from __future__ import annotations` 支持前向引用

**异步模式：**
- 所有网络 I/O 必须异步（httpx.AsyncClient）
- **外部 API 调用必须设置超时**
- 使用 `asyncio.gather()` 进行并行操作

**前端：**
- 仅类型导入：`import type { ... }`
- 网络调用放在 `frontend/src/lib/api.ts`
- 小而专注的组件，优先使用组合

### 关键 API 端点

| 端点 | 用途 |
|------|------|
| `POST /v1/aesthetic` | 标准生成 + 评分 + 增强流程 |
| `POST /v1/pipeline/text2image` | 多模型并行生成 + 评分 |
| `POST /v1/pipeline/image2image` | 参考图分析 + 生成 + 一致性检测 |
| `GET /api/providers` | 列出可用的生成提供商 |
| `GET /api/apps` | 应用列表（来自 `gateway/data.py`） |

### 前端架构

**页面：** `/generate`（文生图）、`/image-compose`（图生图）、`/workspace`（美学画廊）、`/ai-application`（应用广场）

**API 集成：** 所有后端调用通过 `frontend/src/lib/api.ts`，读取 `VITE_AE_API` 环境变量（默认 `http://127.0.0.1:8000`）

**分数显示：** 前端始终显示 1-10 分制（后端内部归一化为 0-1）

## 常见调试任务

**查看豆包 API 日志：**
```bash
tail -f logs/doubao_events.jsonl | jq .
```

**查看管线执行日志：**
```bash
tail -f logs/pipeline_runs.jsonl | jq .
```

**测试单个提供商：**
```bash
pytest tests/Qwen_test.py -v
```

**检查 API 密钥配置：**
网关启动时会记录 API 密钥是否存在。检查日志中的：
```
DASHSCOPE_API_KEY (start): sk-...
```

## 关键注意事项

1. **豆包 API 密钥格式：** 必须包含 "Bearer " 前缀：`ARK_API_KEY="Bearer xxxxx"`

2. **评分维度名称：** 内部系统使用 `contrast_score`、`color_score` 等（英文），但豆包返回 `composition`、`light_color` 等。映射在 `doubao_client.py` 中处理。

3. **Prompt 模板：** `prompts/doubao_aesthetic.prompt` 定义评分标准。修改会影响所有美学评估。

4. **顺序生成模式：** 豆包 Seedream 支持在图生图管线中启用 `sequential_mode` 时一次生成最多 15 张图片。

5. **占位模块：** 多个评分模块（color_score、contrast_score 服务）是占位实现，返回模拟分数。只有 `holistic`（通过豆包）和 MNet 是真实实现。

6. **Mock 数据：** `gateway/data.py` 为 `/api/apps`、`/api/works`、`/api/user/{id}` 提供 Mock 数据以支持前端开发。

## 添加新提供商示例

在 `services/generate/adapters/` 创建新文件：

```python
from services.generate.adapters.base import BaseProvider
from services.generate.models import GenerateRequestPayload

class MyProviderAdapter(BaseProvider):
    @property
    def name(self) -> str:
        return "my_provider"

    async def generate(self, request: GenerateRequestPayload) -> Dict[str, Any]:
        # 实现生成逻辑
        return {
            "status": "success",
            "images": [url1, url2],
            "metadata": {"model": "my-model"}
        }
```

然后在 `services/generate/__init__.py` 注册：
```python
from services.generate.adapters.my_provider import MyProviderAdapter

_PROVIDERS = {
    # ... 现有提供商
    "my_provider": MyProviderAdapter(),
}
```
