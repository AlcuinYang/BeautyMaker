# AestheticsEngine · 美学引擎

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg"/>
  <img src="https://img.shields.io/badge/React-19.1-61DAFB.svg"/>
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688.svg"/>
  <img src="https://img.shields.io/badge/License-MIT-green.svg"/>
</p>

**AI-native platform for multi-provider image generation and aesthetic evaluation research**

**AI 原生多模型图像生成与美学评估研究平台**

[English](#english) · [中文](#中文)

---

## English

### Overview

AestheticsEngine is a research platform exploring **aesthetic model applications** through multi-provider image generation and AI-powered quality evaluation. It addresses key challenges in AIGC workflows:

- **Multi-provider coordination**: Parallel generation across 6+ providers (DALL-E, Qwen, Seedream, Gemini, Stable Diffusion)
- **Objective quality assessment**: AI-driven evaluation of AIGC-specific defects (anatomical errors, artifacts, physics violations)
- **Automated selection**: Best candidate identification with comparative analysis
- **Research infrastructure**: JSONL logging, modular scoring, extensible provider architecture

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (React 19 + Vite + Tailwind)                  │
│  ├─ Text2Image Workspace                                │
│  ├─ Image2Image Workspace                               │
│  └─ Aesthetic Analysis Dashboard                        │
└─────────────────┬───────────────────────────────────────┘
                  │ REST API
┌─────────────────┴───────────────────────────────────────┐
│  API Gateway (FastAPI)                                   │
│  ├─ /v1/pipeline/text2image                             │
│  ├─ /v1/pipeline/image2image                            │
│  └─ /api/providers                                      │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────────┐
│  Service Orchestrator                                    │
│  ├─ Text2Image Pipeline (parallel generation)           │
│  ├─ Image2Image Pipeline (reference analysis)           │
│  └─ Scoring Aggregator (Doubao Vision + fallbacks)      │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────────┐
│  Provider Layer (6 adapters)                             │
│  ├─ DALL-E (OpenRouter)      ├─ Qwen (DashScope)       │
│  ├─ Nano Banana (OpenRouter) ├─ Wan (DashScope)        │
│  ├─ Doubao Seedream (ARK)    └─ Stable Diffusion       │
└─────────────────────────────────────────────────────────┘
```

### Core Features

#### 1. Multi-Provider Generation
- **Text2Image Pipeline**: Parallel generation across 1-4 providers, automatic retry with semaphore control
- **Image2Image Pipeline**: Reference analysis → prompt fusion → consistency verification
- **Sequential Generation**: Seedream 4.0 supports up to 15 images in one API call

#### 2. Aesthetic Evaluation System
**Primary Scorer: Doubao Vision** (ByteDance multimodal LLM)
- 5 AIGC-specific dimensions + holistic score (1-10 scale)
- Structured JSON output with Chinese commentary
- Veto mechanism: Anatomical errors automatically cap final score

**Scoring Dimensions**:
| Dimension | Internal Key | Description |
|-----------|--------------|-------------|
| 语义忠实度 | `quality_score` | Prompt adherence |
| 结构合理性 | `clarity_eval` | Anatomical integrity (hands, faces) |
| 物理逻辑 | `contrast_score` | Light, shadow, perspective |
| 画面纯净度 | `noise_eval` | Artifacts, noise, garbled text |
| 艺术美感 | `color_score` | Composition, color harmony |
| 综合评分 | `holistic` | Weighted average |

**Formula**:
```
final_score = 0.3 × anatomical_integrity
            + 0.3 × prompt_adherence
            + 0.2 × aesthetic_value
            + 0.2 × cleanliness

IF anatomical_integrity < 6.0:
    final_score = min(final_score, 5.0)  # Veto mechanism
```

**Fallback Strategy**: Doubao Vision → MNet holistic → Placeholder modules

#### 3. Comparative Review
- AI-generated explanations comparing best vs worst candidates
- Evidence-based analysis citing specific scores
- Context-aware prompts (artistic vs commercial)

#### 4. Provider Ecosystem

| Provider | Model | API | Capabilities |
|----------|-------|-----|--------------|
| DALL-E | GPT-5-Image | OpenRouter | text2image |
| Nano Banana | Gemini-3-Pro-Image | OpenRouter | text2image, image2image |
| Qwen | Qwen-Image | DashScope | text2image, image2image |
| Wan | Wanxiang 2.5 | DashScope | text2image, image2image |
| Seedream | Seedream 4.0 | ARK | text2image, image2image, sequential |
| Stable Diffusion | SDXL | Self-hosted | text2image |

### Quick Start

#### Prerequisites
- Python 3.10+
- Node.js 20.19+
- API Keys: At least `ARK_API_KEY` (for scoring) + one generation provider

#### Backend Setup
```bash
git clone https://github.com/AlcuinYang/AestheticsEngine.git
cd AestheticsEngine

python3.10 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -e .[dev]

# Required: Doubao for scoring
export ARK_API_KEY="Bearer YOUR_DOUBAO_KEY"
export HOLISTIC_MODEL="doubao-seed-1-6-vision-250815"
export HOLISTIC_PROMPT="prompts/doubao_aesthetic.prompt"

# Optional: Generation providers
export DASHSCOPE_API_KEY="sk-YOUR_DASHSCOPE_KEY"    # Qwen, Wan
export OPENROUTER_API_KEY="sk-YOUR_OPENROUTER_KEY"  # DALL-E, Nano Banana

uvicorn gateway.main:app --reload --host 0.0.0.0 --port 8000
```

API Docs: http://localhost:8000/docs

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

Optional: Set `VITE_AE_API=http://localhost:8000` for custom backend URL

### Usage Example

#### Text2Image API
```bash
curl -X POST http://localhost:8000/v1/pipeline/text2image \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A serene Japanese garden with cherry blossoms",
    "providers": ["dalle", "qwen", "nano_banana"],
    "num_candidates": 3,
    "params": {"ratio": "16:9"}
  }'
```

**Response**:
```json
{
  "best_image_url": "data:image/png;base64,...",
  "best_provider": "dalle",
  "candidates": [
    {
      "provider": "dalle",
      "image_url": "...",
      "composite_score": 0.87,
      "scores": {
        "quality_score": 0.9,
        "clarity_eval": 0.85,
        "contrast_score": 0.88,
        "noise_eval": 0.92,
        "color_score": 0.83,
        "holistic": 0.87
      },
      "comments": {
        "quality_score": "提示词还原度高",
        "clarity_eval": "结构完整无缺陷",
        ...
      }
    }
  ],
  "review": "Image A scored 9.0 in composition vs Image B's 6.8..."
}
```

### Development

#### Testing
```bash
# Backend
pytest                                                   # All tests
pytest tests/test_pipeline_endpoint.py -v               # Pipeline tests
ruff check .                                             # Linting

# Frontend
cd frontend
npm run lint                                             # ESLint
npm run build                                            # Production build
```

#### Monitoring Logs
```bash
tail -f logs/doubao_events.jsonl | jq '.'     # Doubao API calls
tail -f logs/pipeline_runs.jsonl | jq '.'     # Pipeline executions
```

### Adding New Providers

**3-Step Process**:

1. **Create Adapter** (`services/generate/adapters/your_provider.py`)
```python
from services.generate.adapters.base import BaseProvider
from services.generate.models import GenerateRequestPayload

class YourProvider(BaseProvider):
    name = "your_provider"

    async def generate(self, request: GenerateRequestPayload):
        # Implementation
        return {"status": "success", "images": [...], "metadata": {...}}
```

2. **Register** (`services/generate/__init__.py`)
```python
from services.generate.adapters.your_provider import YourProvider

_REGISTRY = {
    ...
    YourProvider.name: YourProvider(),
}
```

3. **Add Metadata** (`services/generate/routes/provider_info.py`)
```python
PROVIDER_META = {
    ...
    "your_provider": {
        "display_name": "Your Provider",
        "description": "Description",
        "category": "image_generation",
        "is_free": False,
        "endpoint": "https://api.example.com",
    },
}
```

### Project Structure
```
AestheticsEngine/
├── frontend/                    # React frontend
│   ├── src/components/         # UI components
│   ├── src/hooks/              # Pipeline orchestration
│   └── src/lib/                # API client
├── services/
│   ├── generate/adapters/      # 6 provider implementations
│   ├── scoring/                # Doubao client + aggregator
│   ├── pipeline/               # Text2Image/Image2Image
│   ├── selector/               # Best candidate selection
│   └── reviewer/               # Comparative analysis
├── gateway/
│   ├── main.py                 # FastAPI app
│   └── orchestrator.py         # Routing
├── prompts/
│   └── doubao_aesthetic.prompt # Scoring template
├── logs/                        # JSONL event logs
└── tests/                       # Backend tests
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ARK_API_KEY` | ✅ | Doubao API key (include "Bearer " prefix) |
| `HOLISTIC_MODEL` | ✅ | Doubao scoring model ID |
| `HOLISTIC_PROMPT` | ✅ | Path to scoring prompt template |
| `DASHSCOPE_API_KEY` | - | Alibaba DashScope (Qwen, Wan) |
| `OPENROUTER_API_KEY` | - | OpenRouter (DALL-E, Nano Banana) |
| `OPENROUTER_PROXY_URL` | - | OpenRouter proxy (default: `http://127.0.0.1:7897`) |
| `VITE_AE_API` | - | Frontend API URL (default: `http://127.0.0.1:8000`) |

### Contributing

We welcome contributions! Please:
1. Fork and create a feature branch
2. Follow `CONTRIBUTING.md` guidelines (type hints, async patterns, logging rules)
3. Run tests: `pytest` + `ruff check .`
4. Submit PR with clear description

**Multi-AI Collaboration**: This project supports development by multiple AI assistants. See `AGENTS.md` for role definitions.

### License

MIT License © 2024

Contact: alcuinyang@gmail.com

---

## 中文

### 项目概述

AestheticsEngine（美学引擎）是一个**美学模型应用研究平台**，通过多模型图像生成与 AI 驱动的质量评估探索 AIGC 工作流中的关键问题：

- **多模型协调**：并行调用 6+ 图像生成提供商（DALL-E、Qwen、Seedream、Gemini、Stable Diffusion）
- **客观质量评估**：AI 驱动的 AIGC 特定缺陷检测（解剖错误、伪影、物理违规）
- **自动选优**：基于对比分析的最优候选识别
- **研究基础设施**：JSONL 日志、模块化评分、可扩展的提供商架构

### 核心功能

#### 1. 多模型生成管线
- **文生图管线**：1-4 个提供商并行生成，信号量控制 + 自动重试
- **图生图管线**：参考图分析 → 提示词融合 → 一致性验证
- **顺序生成**：Seedream 4.0 单次 API 调用支持最多 15 张图像

#### 2. 美学评估系统
**主评分器：豆包 Vision**（字节跳动多模态 LLM）
- 5 个 AIGC 专属维度 + 综合评分（1-10 分制）
- 结构化 JSON 输出 + 中文评论
- 否决机制：解剖错误自动限制最终得分上限

**评分维度**：
| 维度 | 内部键 | 说明 |
|------|--------|------|
| 语义忠实度 | `quality_score` | 提示词还原度 |
| 结构合理性 | `clarity_eval` | 解剖完整性（手部、面部） |
| 物理逻辑 | `contrast_score` | 光影、透视准确性 |
| 画面纯净度 | `noise_eval` | 伪影、噪点、乱码文字 |
| 艺术美感 | `color_score` | 构图、色彩协调性 |
| 综合评分 | `holistic` | 加权平均值 |

**评分公式**：
```
final_score = 0.3 × 解剖完整性
            + 0.3 × 语义忠实度
            + 0.2 × 艺术美感
            + 0.2 × 画面纯净度

若 解剖完整性 < 6.0：
    final_score = min(final_score, 5.0)  # 否决机制
```

**降级策略**：豆包 Vision → MNet 综合评分 → 占位模块

#### 3. 对比点评
- AI 生成的最优/最差候选对比解释
- 基于具体评分的证据分析
- 上下文感知提示词（艺术 vs 商业）

#### 4. 提供商生态

| 提供商 | 模型 | API | 能力 |
|--------|------|-----|------|
| DALL-E | GPT-5-Image | OpenRouter | 文生图 |
| Nano Banana | Gemini-3-Pro-Image | OpenRouter | 文生图、图生图 |
| Qwen | Qwen-Image | DashScope | 文生图、图生图 |
| Wan | 通义万相 2.5 | DashScope | 文生图、图生图 |
| Seedream | Seedream 4.0 | ARK | 文生图、图生图、顺序生成 |
| Stable Diffusion | SDXL | 自托管 | 文生图 |

### 快速开始

#### 环境要求
- Python 3.10+
- Node.js 20.19+
- API 密钥：至少需要 `ARK_API_KEY`（评分）+ 一个生成提供商

#### 后端启动
```bash
git clone https://github.com/AlcuinYang/AestheticsEngine.git
cd AestheticsEngine

python3.10 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -e .[dev]

# 必需：豆包评分
export ARK_API_KEY="Bearer YOUR_DOUBAO_KEY"
export HOLISTIC_MODEL="doubao-seed-1-6-vision-250815"
export HOLISTIC_PROMPT="prompts/doubao_aesthetic.prompt"

# 可选：生成提供商
export DASHSCOPE_API_KEY="sk-YOUR_DASHSCOPE_KEY"    # Qwen、Wan
export OPENROUTER_API_KEY="sk-YOUR_OPENROUTER_KEY"  # DALL-E、Nano Banana

uvicorn gateway.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档：http://localhost:8000/docs

#### 前端启动
```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

可选：设置 `VITE_AE_API=http://localhost:8000` 指定后端地址

### 使用示例

#### 文生图 API
```bash
curl -X POST http://localhost:8000/v1/pipeline/text2image \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "宁静的日本庭院，樱花盛开",
    "providers": ["dalle", "qwen", "nano_banana"],
    "num_candidates": 3,
    "params": {"ratio": "16:9"}
  }'
```

**响应示例**：
```json
{
  "best_image_url": "data:image/png;base64,...",
  "best_provider": "dalle",
  "candidates": [
    {
      "provider": "dalle",
      "image_url": "...",
      "composite_score": 0.87,
      "scores": {
        "quality_score": 0.9,
        "clarity_eval": 0.85,
        "contrast_score": 0.88,
        "noise_eval": 0.92,
        "color_score": 0.83,
        "holistic": 0.87
      },
      "comments": {
        "quality_score": "提示词还原度高",
        "clarity_eval": "结构完整无缺陷",
        ...
      }
    }
  ],
  "review": "图像 A 在构图（9.0分）上明显优于图像 B（6.8分）..."
}
```

### 开发指南

#### 测试
```bash
# 后端
pytest                                                   # 全部测试
pytest tests/test_pipeline_endpoint.py -v               # 管线测试
ruff check .                                             # 代码检查

# 前端
cd frontend
npm run lint                                             # ESLint
npm run build                                            # 生产构建
```

#### 日志监控
```bash
tail -f logs/doubao_events.jsonl | jq '.'     # 豆包 API 调用
tail -f logs/pipeline_runs.jsonl | jq '.'     # 管线执行
```

### 添加新提供商

**三步流程**：

1. **创建适配器** (`services/generate/adapters/your_provider.py`)
```python
from services.generate.adapters.base import BaseProvider
from services.generate.models import GenerateRequestPayload

class YourProvider(BaseProvider):
    name = "your_provider"

    async def generate(self, request: GenerateRequestPayload):
        # 实现逻辑
        return {"status": "success", "images": [...], "metadata": {...}}
```

2. **注册** (`services/generate/__init__.py`)
```python
from services.generate.adapters.your_provider import YourProvider

_REGISTRY = {
    ...
    YourProvider.name: YourProvider(),
}
```

3. **添加元数据** (`services/generate/routes/provider_info.py`)
```python
PROVIDER_META = {
    ...
    "your_provider": {
        "display_name": "你的提供商",
        "description": "描述信息",
        "category": "image_generation",
        "is_free": False,
        "endpoint": "https://api.example.com",
    },
}
```

### 项目结构
```
AestheticsEngine/
├── frontend/                    # React 前端
│   ├── src/components/         # UI 组件
│   ├── src/hooks/              # 管线编排
│   └── src/lib/                # API 客户端
├── services/
│   ├── generate/adapters/      # 6 个提供商实现
│   ├── scoring/                # 豆包客户端 + 聚合器
│   ├── pipeline/               # 文生图/图生图
│   ├── selector/               # 最优候选选择
│   └── reviewer/               # 对比分析
├── gateway/
│   ├── main.py                 # FastAPI 应用
│   └── orchestrator.py         # 路由
├── prompts/
│   └── doubao_aesthetic.prompt # 评分模板
├── logs/                        # JSONL 事件日志
└── tests/                       # 后端测试
```

### 环境变量

| 变量 | 必需 | 说明 |
|------|------|------|
| `ARK_API_KEY` | ✅ | 豆包 API 密钥（需包含 "Bearer " 前缀） |
| `HOLISTIC_MODEL` | ✅ | 豆包评分模型 ID |
| `HOLISTIC_PROMPT` | ✅ | 评分提示词模板路径 |
| `DASHSCOPE_API_KEY` | - | 阿里云 DashScope（Qwen、Wan） |
| `OPENROUTER_API_KEY` | - | OpenRouter（DALL-E、Nano Banana） |
| `OPENROUTER_PROXY_URL` | - | OpenRouter 代理（默认：`http://127.0.0.1:7897`） |
| `VITE_AE_API` | - | 前端 API 地址（默认：`http://127.0.0.1:8000`） |

### 贡献指南

欢迎贡献！请：
1. Fork 并创建功能分支
2. 遵循 `CONTRIBUTING.md` 指南（类型注解、异步模式、日志规则）
3. 运行测试：`pytest` + `ruff check .`
4. 提交清晰描述的 PR

**多 AI 协作**：本项目支持多个 AI 助手协同开发。详见 `AGENTS.md`。

### 许可证

MIT License © 2024

联系方式：alcuinyang@gmail.com

---

## Documentation

- 📖 [完整文档](doc/项目完整文档.md) - Comprehensive Chinese documentation
- 🚀 [Quick Start](QUICKSTART.md) - Fast setup guide
- 🤝 [Contributing](CONTRIBUTING.md) - Development guidelines
- 🤖 [AI Collaboration](AGENTS.md) - Multi-AI development guide
- 📚 [API Docs](http://localhost:8000/docs) - Interactive API documentation (requires running backend)
