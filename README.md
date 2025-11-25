# 🎨 BeautyMaker (美学引擎)

<div align="center">

**AI-Powered Aesthetic Evaluation & Multi-Provider Image Generation Engine**

**集成图像生成提供商的智能美学评估引擎**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-blue.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[English](#english) | [中文](#中文)

</div>

---

## 中文

### 📖 项目简介

BeautyMaker（美学引擎）是一个**模块化的 AI 美学评估和图像生成平台**，专为需要高质量图像生成和专业美学评估的场景设计。

#### 🌟 核心优势

- **🎯 多维美学评分**：集成豆包 Vision 模型，提供 **5 维专业美学评分 + 中文点评**
  - 构图表达（Composition）
  - 光影色彩（Light & Color）
  - 风格一致性（Style Coherence）
  - 情感表达（Emotional Impact）
  - 清晰完整度（Clarity & Integrity）

- **🚀 13+ 图像生成提供商**：一个接口，调用多个主流 AI 图像生成服务
  - 通义千问（Qwen）、豆包 Seedream、OpenAI DALL·E、Gemini Flash
  - HuggingFace、Stability AI 等

- **⚡ 智能管线系统**
  - **文生图管线**：多模型并行生成 → 美学评分 → 自动选优
  - **图生图管线**：参考图分析 → Prompt 融合 → 一致性检测

- **🎨 Apple 风格前端**：React 19 + TypeScript + Tailwind CSS，流畅优雅的用户体验

### 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    前端应用层 (React 19)                  │
│  文生图工作台 | 图生图工作台 | 美学作品展示 | 应用广场    │
└────────────────────┬────────────────────────────────────┘
                     │ REST API
                     ↓
┌─────────────────────────────────────────────────────────┐
│                  API 网关层 (FastAPI)                     │
│         /v1/aesthetic | /v1/pipeline/* | /api/*         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                 服务编排层 (Orchestrator)                 │
│          协调生成、评分、增强、选优四大服务                │
└───┬─────────┬─────────┬─────────┬────────────────────────┘
    │         │         │         │
    ↓         ↓         ↓         ↓
┌────────┐┌────────┐┌────────┐┌────────┐
│生成服务││评分聚合││增强服务││选优服务│
│13提供商││豆包优先││超分预留││智能选择│
└────────┘└────────┘└────────┘└────────┘
```

### 🚀 快速开始

#### 环境要求

- Python 3.10+
- Node.js 20.19+
- API 密钥（至少一个）：
  - 豆包：`ARK_API_KEY`（推荐，用于美学评分）
  - 通义千问：`DASHSCOPE_API_KEY`
  - OpenAI：`OPENAI_API_KEY`

#### 后端启动

```bash
# 1. 克隆项目
git clone git@github.com:AlcuinYang/BeautyMaker.git
cd BeautyMaker

# 2. 安装依赖
pip install -e .[dev]

# 3. 配置环境变量
export ARK_API_KEY="Bearer your_doubao_key"
export DASHSCOPE_API_KEY="sk-your_qwen_key"
export HOLISTIC_MODEL="doubao-seed-1-6-vision"
export HOLISTIC_PROMPT="prompts/doubao_aesthetic.prompt"

# 4. 启动服务
uvicorn gateway.main:app --reload --host 0.0.0.0 --port 8000
```

访问 API 文档：http://localhost:8000/docs

#### 前端启动

```bash
cd frontend
npm install
npm run dev
```

访问应用：http://localhost:5173

#### 🐳 Docker 快速部署

```bash
cd infra
docker-compose up --build
```

### 📚 核心功能

#### 1️⃣ 文生图智能管线

```bash
POST /v1/pipeline/text2image
```

**特点：**
- 支持 1-4 个提供商并行生成
- 每个提供商可生成 1-6 张候选图
- 豆包 Vision 自动评分和点评
- 智能选择最佳结果

**示例：**
```json
{
  "prompt": "一只猫骑着自行车，梵高风格",
  "providers": ["qwen", "doubao_seedream"],
  "num_candidates": 3,
  "params": {
    "ratio": "16:9"
  }
}
```

#### 2️⃣ 图生图营销管线

```bash
POST /v1/pipeline/image2image
```

**特点：**
- 豆包 Vision 智能分析参考图（产品、风格、关键词）
- 自动融合 Prompt 模板库
- 主体一致性检测（参考图 vs 生成图）
- 在线学习：根据美学评分更新模板权重

**应用场景：**
- 电商营销图智能生成
- 产品图风格迁移
- 创意广告素材制作

#### 3️⃣ 豆包多维美学评分

**评分系统：**
- 5 个美学维度（1-10 分制）
- 每个维度附带专业中文点评（≤50 字）
- 综合分计算：`0.75 × 美学均分 + 0.25 × 清晰度分`

**降级策略：**
- 优先调用豆包 Vision API
- 失败时自动降级到技术评分模块（MNet 等）

### 🛠️ 技术栈

**后端：**
- FastAPI 0.110+ (Python 3.10+)
- httpx (异步 HTTP 客户端)
- Pydantic 2.6+ (数据验证)
- Pillow 10.0+ (图像处理)

**前端：**
- React 19.1 + TypeScript 5.9
- Vite 7.1 (构建工具)
- Tailwind CSS 3.4 (样式框架)
- Framer Motion 11.11 (动画)
- Recharts 2.15 (图表)

**AI 集成：**
- 豆包 Vision（美学评分 + 图像分析）
- 13+ 主流图像生成 API

### 📖 文档

- [CLAUDE.md](./CLAUDE.md) - AI 助手开发指南
- [CONTRIBUTING.md](./CONTRIBUTING.md) - 贡献指南和代码规范
- [完整项目文档](./doc/项目完整文档.md) - 详细架构和 API 文档
- [项目笔记](./doc/PROJECT_NOTES.md) - 开发日志

### 🗂️ 项目结构

```
BeautyMaker/
├── gateway/              # API 网关层
│   ├── main.py          # FastAPI 主应用
│   ├── orchestrator.py  # 服务编排器
│   └── schemas.py       # 请求/响应模型
├── services/            # 核心服务层
│   ├── generate/        # 图像生成服务（13 个适配器）
│   ├── scoring/         # 美学评分聚合器
│   ├── pipeline/        # 智能管线
│   ├── enhancer/        # 图像增强
│   └── selector/        # 智能选优
├── frontend/            # React 前端应用
│   ├── src/components/  # UI 组件
│   ├── src/pages/       # 页面路由
│   └── src/lib/         # API 封装
├── config/              # 配置文件
├── prompts/             # AI 提示词模板
├── tests/               # 测试代码
└── infra/               # Docker 部署配置
```

### 🔧 开发指南

#### 添加新的图像生成提供商

1. 在 `services/generate/adapters/` 创建适配器：

```python
from services.generate.adapters.base import BaseProvider

class MyProviderAdapter(BaseProvider):
    @property
    def name(self) -> str:
        return "my_provider"

    async def generate(self, request) -> Dict[str, Any]:
        # 实现生成逻辑
        return {"status": "success", "images": [...]}
```

2. 在 `services/generate/__init__.py` 注册
3. 在 `services/generate/routes/provider_info.py` 添加元数据

详细说明见 [CONTRIBUTING.md](./CONTRIBUTING.md)

#### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_pipeline_endpoint.py -v

# 测试单个提供商
pytest tests/Qwen_test.py -v
```

### 📊 性能特点

- **异步并发架构**：多提供商并行调用，总耗时 ≈ 单个提供商耗时
- **智能降级**：豆包 API 失败时自动回退到技术评分
- **事件日志**：完整追溯所有 API 调用（`logs/doubao_events.jsonl`）
- **在线学习**：Prompt 模板权重自动优化

### 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

请遵循 [CONTRIBUTING.md](./CONTRIBUTING.md) 中的代码规范。

### 📝 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

### 🙏 致谢

- [豆包大模型](https://www.volcengine.com/docs/82379) - 提供强大的美学评分能力
- [通义千问](https://help.aliyun.com/zh/dashscope/) - 高质量图像生成
- [FastAPI](https://fastapi.tiangolo.com/) - 优秀的 Python Web 框架

---

## English

### 📖 About

BeautyMaker (AestheticsEngine) is a **modular AI aesthetic evaluation and image generation platform** designed for scenarios requiring high-quality image generation and professional aesthetic assessment.

#### 🌟 Key Features

- **🎯 Multi-Dimensional Aesthetic Scoring**: Powered by Doubao Vision model
  - 5 professional aesthetic dimensions with Chinese commentary
  - Composition, Light & Color, Style Coherence, Emotional Impact, Clarity

- **🚀 13+ Image Generation Providers**: One API, multiple AI services
  - Qwen, Doubao Seedream, OpenAI DALL·E, Gemini Flash
  - Pollinations (free, no API key required), HuggingFace, Stability AI, etc.

- **⚡ Intelligent Pipelines**
  - **Text-to-Image**: Multi-model parallel generation → Scoring → Auto selection
  - **Image-to-Image**: Reference analysis → Prompt fusion → Consistency check

- **🎨 Apple-Style Frontend**: React 19 + TypeScript + Tailwind CSS

### 🚀 Quick Start

#### Prerequisites

- Python 3.10+
- Node.js 20.19+
- API Keys (at least one):
  - Doubao: `ARK_API_KEY` (recommended for aesthetic scoring)
  - Qwen: `DASHSCOPE_API_KEY`
  - OpenAI: `OPENAI_API_KEY`

#### Backend Setup

```bash
# Clone repository
git clone git@github.com:AlcuinYang/BeautyMaker.git
cd BeautyMaker

# Install dependencies
pip install -e .[dev]

# Configure environment
export ARK_API_KEY="Bearer your_doubao_key"
export DASHSCOPE_API_KEY="sk-your_qwen_key"
export HOLISTIC_MODEL="doubao-seed-1-6-vision"
export HOLISTIC_PROMPT="prompts/doubao_aesthetic.prompt"

# Start server
uvicorn gateway.main:app --reload --host 0.0.0.0 --port 8000
```

API Docs: http://localhost:8000/docs

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Visit: http://localhost:5173

#### 🐳 Docker Deployment

```bash
cd infra
docker-compose up --build
```

### 📚 Core APIs

#### Text-to-Image Pipeline

```bash
POST /v1/pipeline/text2image
```

Example:
```json
{
  "prompt": "A cat riding a bicycle, Van Gogh style",
  "providers": ["qwen", "doubao_seedream"],
  "num_candidates": 3,
  "params": {
    "ratio": "16:9"
  }
}
```

#### Image-to-Image Pipeline

```bash
POST /v1/pipeline/image2image
```

Features:
- AI-powered reference image analysis
- Automatic prompt template fusion
- Subject consistency verification
- Online learning for template optimization

### 🛠️ Tech Stack

**Backend:**
- FastAPI 0.110+ (Python 3.10+)
- httpx (Async HTTP)
- Pydantic 2.6+ (Data validation)
- Pillow 10.0+ (Image processing)

**Frontend:**
- React 19.1 + TypeScript 5.9
- Vite 7.1
- Tailwind CSS 3.4
- Framer Motion 11.11
- Recharts 2.15

**AI Integration:**
- Doubao Vision (Aesthetic scoring + Image analysis)
- 13+ mainstream image generation APIs

### 📖 Documentation

- [CLAUDE.md](./CLAUDE.md) - AI Assistant Development Guide
- [CONTRIBUTING.md](./CONTRIBUTING.md) - Contribution Guidelines
- [Complete Documentation](./doc/项目完整文档.md) - Detailed Architecture (Chinese)
- [Project Notes](./doc/PROJECT_NOTES.md) - Development Log (Chinese)

### 🤝 Contributing

Contributions are welcome! Please check [CONTRIBUTING.md](./CONTRIBUTING.md) for code standards.

### 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details

### 🙏 Acknowledgments

- [Doubao AI](https://www.volcengine.com/docs/82379) - Powerful aesthetic scoring
- [Qwen](https://help.aliyun.com/zh/dashscope/) - High-quality image generation
- [FastAPI](https://fastapi.tiangolo.com/) - Excellent Python web framework

---

<div align="center">

**Made with ❤️ by the BeautyMaker Team**

⭐ Star us on GitHub if you find this project useful!

</div>
