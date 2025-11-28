# AestheticsEngine · 美学引擎

AI-native workflow for **multi-provider image generation**, **aesthetic evaluation**, and **e-commerce creative pipelines**.

[中文说明](#中文说明)

---

## ✨ Feature Highlights

- **Smart Pipelines**
  - `text2image`: multi-provider parallel generation → Doubao Vision scoring → automatic best-shot selection & comparative review.
  - `image2image`: reference analysis → prompt fusion → sequential generation (Seedream i2i) → consistency check → scoring.
- **AIGC-Native Metrics**: 5 visible dimensions + holistic score with Chinese comments; labels unified across radar charts, candidate list, and API responses.
- **Smart Upload UX**: category selection → shooting guide → drag & drop upload → preview + confirmation.
- **Global Progress Bar**: fake-progress simulation (steps 0–2), hold during generation, fast-forward (3–5) once the API returns.
- **Provider Abstraction Layer**: 13+ adapters (Qwen, Doubao Seedream, Wanxiang, Nano Banana, OpenAI DALL·E, etc.) with per-provider retry logic.
- **Developer-Ready APIs**: FastAPI entrypoints, async httpx clients, JSONL execution logs, and typed models for every request/response.

---

## 🏗️ Architecture Overview

```
Client (React 19 + Vite)
│  ├─ Smart Upload, Text2Image Workspace, ImageCompose Workspace
│  └─ /frontend/src/components /hooks /lib
│
API Gateway (FastAPI)
│  ├─ /v1/pipeline/text2image
│  ├─ /v1/pipeline/image2image
│  ├─ /v1/aesthetic
│  └─ /api/providers /api/apps
│
Orchestrator
│  ├─ services/pipeline/text2image.py
│  ├─ services/pipeline/image2image.py
│  └─ services/scoring/aggregator.py
│
Service Layer
│  ├─ Generation adapters (services/generate/adapters/*)
│  ├─ Doubao scoring client (services/scoring/holistic)
│  ├─ Selector service
│  └─ Reviewer / tools
└─ Logs
   ├─ logs/doubao_events.jsonl
   └─ logs/pipeline_runs.jsonl
```

---

## 🚀 Quick Start

### Backend

```bash
git clone git@github.com:AlcuinYang/BeautyMaker.git
cd BeautyMaker

python3.10 -m venv .venv && source .venv/bin/activate
pip install -e .[dev]

export ARK_API_KEY="Bearer xxx"          # Seedream + Vision
export DASHSCOPE_API_KEY="sk-xxx"        # Tongyi Qianwen / Wanxiang
export OPENAI_API_KEY="sk-xxx"           # DALL·E (optional)
export HOLISTIC_MODEL="doubao-seed-1-6-vision"
export HOLISTIC_PROMPT="prompts/doubao_aesthetic.prompt"

uvicorn gateway.main:app --host 0.0.0.0 --port 8000 --reload
```

- Docs: `http://localhost:8000/docs`
- JSON logs: `logs/doubao_events.jsonl`, `logs/pipeline_runs.jsonl`

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173 (uses VITE_AE_API or default 8000)
```

---

## ⚙️ Pipelines & Flows

### 1. Text-to-Image (`services/pipeline/text2image.py`)
1. (Optional) Prompt expansion stub.
2. Parallel generation across selected providers, each with semaphore + retry.
3. `ScoringAggregator` executes Doubao holistic scoring (and fallback modules), storing per-image results.
4. `SelectorService` identifies the best candidate.
5. Optional comparative review (Doubao Vision compares winner vs. lowest score).
6. Response: best image, candidates with module-level scores, summary, review, prompt metadata.

### 2. Image-to-Image (`services/pipeline/image2image.py`)
1. Reference analysis via Doubao Vision (platform / product / style keywords).
2. Provider-specific generation (Seedream sequential mode, others one-by-one).
3. Consistency verification (candidate vs reference) via Doubao chat completion.
4. Scoring aggregator + ordered results (group mode available).
5. Pipeline events logged to JSONL for observability.
6. Frontend consumes results via `useImageCompose` hook and `ImageComposeWorkspace`.

### 3. Aesthetic Scoring (`services/scoring/`)
- Doubao Vision prioritized; fallback modules (MNet, placeholder services) keep pipeline alive.
- Score normalization: Doubao returns 1–10 → normalized to 0–1 internally → 1–10 shown on UI.
- Dimension mapping (internal → Display):
  - `contrast_score` → 物理逻辑
  - `color_score` → 艺术美感
  - `clarity_eval` → 结构合理性
  - `quality_score` → 语义忠实度
  - `noise_eval` → 画面纯净度
  - `holistic` → 综合评分

---

## 🧩 Frontend Modules

- `TextToImageWorkspace.tsx`: model selection, prompt input, reference uploads, pipeline timeline, candidate comparisons, `AestheticAnalysisCard`.
- `ImageComposeWorkspace.tsx`: Smart Upload modal, ratio/model/quantity controls, global progress bar integration, sequential results gallery.
- `SmartUploadModal.tsx`: multi-step UX with drag & drop, guide text, preview & confirm.
- `GlobalProgressBar.tsx`: animated step indicator with statuses (`idle`, `processing`, `success`).
- `hooks/usePipeline.ts` & `hooks/useImageCompose.ts`: orchestrate API calls, stage handling, error management.
- `constants/aigcMetrics.ts` & `lib/constants.ts`: single source for metric labels & ordering.

---

## 🔧 Environment Variables

| Variable | Purpose |
| --- | --- |
| `ARK_API_KEY` | Doubao Seedream & Vision API (prefixed with `Bearer `) |
| `DASHSCOPE_API_KEY` | Tongyi Qianwen / Wanxiang generation |
| `OPENAI_API_KEY` | DALL·E provider (optional) |
| `HOLISTIC_MODEL` | Doubao scoring model id |
| `HOLISTIC_PROMPT` | Path to scoring prompt file |
| `GLOBAL_HTTP_PROXY` | Optional proxy for outbound HTTP |
| `VITE_AE_API` | Frontend → Backend base URL |

---

## 📁 Key Directories

```
frontend/
  src/components/          # Workspaces, cards, modals, global UI
  src/hooks/               # Pipeline hooks
  src/lib/                 # API client, constants
  src/pages/               # Route-level containers

services/
  generate/adapters/       # Provider implementations
  scoring/                 # Aggregator + Doubao clients
  pipeline/                # Text2Image / Image2Image orchestrators
  selector/                # Best-candidate logic

gateway/
  main.py                  # FastAPI app
  orchestrator.py          # Pipeline router
  data.py                  # Mock endpoints for frontend
```

---

## 🧪 Development Workflow

```bash
# Type checking, linting, and tests
ruff check .
pytest

# Run specific pipeline tests
pytest tests/test_pipeline_endpoint.py::test_text2image_pipeline -v
pytest tests/test_pipeline_endpoint.py::test_image2image_pipeline -v
```

- Provider testing: `pytest tests/Qwen_test.py -v`
- Observe Doubao API calls: `tail -f logs/doubao_events.jsonl | jq '.'`
- Observe pipeline events: `tail -f logs/pipeline_runs.jsonl | jq '.'`

---

## 🤝 Contributing

1. Fork + branch.
2. Follow `CONTRIBUTING.md` (adapter structure, logging rules, type hints, async conventions).
3. Run tests + lint.
4. Submit PR with context (feature, bug fix, integration).

> This repository is optimized for multi-AI collaboration (Claude, GPT, local models). See `AGENTS.md` for assistant-specific instructions.

---

## 📄 License

MIT License © 2024 BeautyMaker Team.

---

## 中文说明

### 项目简介

AestheticsEngine（美学引擎）面向电商创意、AI 运营和美学质检场景，提供“多模型生成 + 豆包评分 + 智能选优”的一体化管线。前端支撑 Smart Upload、文生图、图生图等工作台，后端基于 FastAPI + 异步 orchestrator 完成生成与评分调度。

### 核心能力

- **双管线：**
  - 文生图（text2image）：多提供商并行 → 豆包 Vision 评分 → 最优候选 + 中文对比点评。
  - 图生图（image2image）：参考图分析 → 顺序生成（Seedream sequential）→ 一致性检测 → 美学评分。
- **美学评分：** 物理逻辑 / 艺术美感 / 结构合理性 / 语义忠实度 / 画面纯净度 / 综合分，全程中文点评，UI 与 API 维度统一。
- **智能交互：** Smart Upload 三步流程、全局进度条假进度（0→2）+ 快速收尾（3→5）、候选卡 / 雷达图一致显示 AIGC 指标。
- **多提供商抽象：** 内置 Qwen、豆包 Seedream、通义万相、Nano Banana、OpenAI DALL·E 等适配器，支持信号量 + 重试机制。
- **可观测性：** `logs/doubao_events.jsonl` 记录豆包调用，`logs/pipeline_runs.jsonl` 记录管线执行摘要。

### 快速开始

#### 后端

```bash
git clone git@github.com:AlcuinYang/BeautyMaker.git
cd BeautyMaker
python3.10 -m venv .venv && source .venv/bin/activate
pip install -e .[dev]

export ARK_API_KEY="Bearer xxx"
export DASHSCOPE_API_KEY="sk-xxx"
export OPENAI_API_KEY="sk-xxx"
export HOLISTIC_MODEL="doubao-seed-1-6-vision"
export HOLISTIC_PROMPT="prompts/doubao_aesthetic.prompt"

uvicorn gateway.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

### 架构图

```
前端 (React + Vite)
 ├─ Smart Upload / 文生图 / 图生图 / Progress Bar
 └─ hooks (usePipeline / useImageCompose)

API 网关 (FastAPI)
 ├─ /v1/pipeline/text2image
 ├─ /v1/pipeline/image2image
 └─ /api/providers /api/apps

服务编排
 ├─ services/pipeline/text2image.py
 ├─ services/pipeline/image2image.py
 └─ services/scoring/aggregator.py

服务层
 ├─ generate/adapters/* (13+ provider)
 ├─ scoring/holistic/doubao_client.py
 └─ selector/service.py

日志
 ├─ logs/doubao_events.jsonl
 └─ logs/pipeline_runs.jsonl
```

### 目录速览

- `frontend/src/components`：工作台、上传模态、候选卡、雷达图等。
- `frontend/src/hooks`：`usePipeline.ts`、`useImageCompose.ts` 控制阶段、错误、复位。
- `services/generate/adapters`：Qwen、Seedream、Wanxiang 等适配器。
- `services/pipeline`：文生图 / 图生图 orchestrator。
- `services/scoring`：评分聚合、Doubao 客户端。
- `gateway/main.py`：FastAPI 实例；`gateway/data.py` 为前端 mock 数据。

### 常见命令

```bash
ruff check .
pytest
pytest tests/test_pipeline_endpoint.py::test_text2image_pipeline -v
pytest tests/test_pipeline_endpoint.py::test_image2image_pipeline -v
```

### 贡献说明

- 遵循 `CONTRIBUTING.md`：适配器拆分、日志脱敏、类型注解、异步请求。
- 前端统一 TypeScript + Tailwind，指标名称自 `constants/aigcMetrics.ts` / `lib/constants.ts`。
- 欢迎提交 Issue / PR 与我们共建美学引擎。若需更详细资料，请查阅 `doc/项目完整文档.md`、`doc/PIPELINE_GUIDE.md`。
