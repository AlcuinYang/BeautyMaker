# 美学引擎项目笔记
_最近更新时间：2025-11-05 23:55 CST_

## 项目概览
- 构建一个集生成、豆包多维审美评分、增强与选优于一体的美学引擎。
- 后端采用 FastAPI，统一对外提供网关接口与 Mock 数据，便于前端联调。
- 服务层包含生成、审美评分、增强、选优等独立模块，可灵活替换接入不同模型。
- 前端使用 React + Vite + Tailwind，提供多页创作工作台，并默认连接到本地 `http://127.0.0.1:8000`。
u
## 主要组件
- **Gateway（`gateway/`）**：`main.py` 负责路由、依赖注入与 Mock API；`orchestrator.py` 串联生成、评分、增强、选优。
- **生成模块（`services/generate/`）**：`service.py` 统一参数与响应，`adapters/` 内含 OpenAI、Pollinations、Qwen、Doubao 等适配器（仍有占位实现待替换）。
- **评分模块（`services/scoring/`）**：`ScoringAggregator` 优先调用 Doubao Vision 模型（`holistic/doubao_client.py`）返回 `composition`、`light_color`、`style_coherence`、`emotional_impact`、`clarity_integrity` 与 `final_score`，并附带点评；若调用失败则回退原 MNet / 技术向评分模块。
- **增强模块（`services/enhancer/service.py`）**：目前仅做清晰度标记，预留未来接入超分、去噪等能力。
- **选优模块（`services/selector/service.py`）**：以美感分（holistic）为主，选出最佳候选；缺失评分时回退到第一张图片。
- **管线模块（`services/pipeline/`）**：文生图智能管线整合 Prompt 扩写（占位）、多模型生成、豆包评分、选优与前端展示结构；图生图“一拍即合”管线补充一致性检测。
- **基础设施（`infra/`）**：包含 Docker Compose、部署脚本与配置模板。

## API 与接口
- `POST /v1/aesthetic`：标准生成 + 审美评分 + 增强入口。
- `POST /v1/pipeline/text2image`：智能文生图管线（多模型、评分、选优、点评汇总）。
- `POST /v1/pipeline/image2image`：图生图营销管线（参考图、模板、一致性评分）。
- Mock 接口：`/api/apps`、`/api/apps/{id}`、`/api/works`、`/api/user/{id}`、`POST /v1/publish`。
- 接口契约集中在 `openapi.yaml` 与各 Pydantic 模型中。

## 前端进展
- 已实现 `/ai-application`、`/ai-detail/:id`、`/generate`、`/image-compose`、`/workspace` 等页面；`/workspace` 使用 Doubao 美学模型并展示瀑布流作品。
- 文生图与图生图页面改为宽屏布局，评分与雷达图统一为 1–10 分制，维度标签与豆包返回保持一致。
- 开发流程：`npm install` → `npm run dev`（推荐 Node 20.19+）；如需连接远程后端，可通过 `VITE_AE_API` 配置。

## 工具与测试
- 安装后端依赖：`pip install -e .[dev]`。
- 启动 API：`uvicorn gateway.main:app --reload`，需配置 `OPENAI_API_KEY`、`DASHSCOPE_API_KEY`、`ARK_API_KEY`/`DOUBAO_API_KEY`，同时设置 Doubao 审美环境变量 `HOLISTIC_MODEL`、`HOLISTIC_PROMPT`、`HOLISTIC_SCORE_TOKEN`。
- 运行测试：`pytest`。
- 前端默认使用 Vite 内建脚手架，可执行 `npm run lint`、`npm run test`。

## 未完事项
- 完善 Doubao 审美接口的高可用策略（重试、缓存、异常降级），并按需持久化点评文本。
- 逐步替换生成适配器中的占位实现，接入真实模型能力。
- 设计生成成果的持久化与素材管理方案。
- 明确部署环境与密钥管理方式，避免在线上暴露敏感信息。

## 功能可见性
- App 列表由 `gateway/data.py` 控制，前端直接消费 `/api/apps`；如需隐藏某功能，可在该文件或前端过滤处理。
- 文生图、图生图与 Aesthetic Workspace 页面均已切换为 1–10 分制，并展示豆包返回的点评文案。

## 进度日志
- 2025-11-03：整理项目结构，完成初版文档。
- 2025-11-04：记录如何隐藏图生视频、风格迁移等功能。
- 2025-11-05（下午）：接入 Doubao 多维审美评分与点评，前端统一维度标签与 10 分制显示，优化生成页布局。
- 2025-11-05（晚间）：删除图生图页面的 Prompt Bank 功能，修复豆包审美接口 400 报错（改用 `messages` 结构并统一图片载入格式），同时为 Doubao 生成与评分模块补充 API Key 诊断日志方便排查环境变量。
- 2025-11-05（深夜）：图生图移除 Prompt 扩写入口，新增「生成组图」开关（豆包 Seedream 支持一次顺序生成至多 15 张）；后端组图模式仅保留美感评分并按分数降序返回，普通模式保持多维评分。
