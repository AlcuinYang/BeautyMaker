# AestheticsEngine 快速启动

几分钟内把后端接口和前端工作台跑起来，默认用 Doubao Seedream 占位返回 + 内置评分模块，即便没有 API Key 也能跑通流程。

## 环境准备
- Python 3.10+，`pip` 与 `uvicorn` 会随依赖安装
- Node.js 20+（前端可选）
- 可选密钥：`DASHSCOPE_API_KEY`/`QWEN_API_KEY`（通义）、`ARK_API_KEY` 或 `DOUBAO_API_KEY`/`HOLISTIC_SCORE_TOKEN`（豆包）、`OPENAI_API_KEY`（DALL·E）

## 启动后端 (FastAPI)
```bash
cd /Users/alcuin/Desktop/美学引擎/AestheticsEngine
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]

# 可选：启用更多生成/审美能力
export DASHSCOPE_API_KEY="sk-xxx"   # 通义千问
export ARK_API_KEY="Bearer xxx"     # 豆包 Seedream & Vision
export OPENAI_API_KEY="sk-xxx"      # DALL·E

uvicorn gateway.main:app --reload --port 8000
```
接口文档：`http://127.0.0.1:8000/docs`

## 启动前端 (Vite + React，可选)
```bash
cd /Users/alcuin/Desktop/美学引擎/AestheticsEngine/frontend
npm install
VITE_AE_API="http://127.0.0.1:8000" npm run dev -- --host --port 5173
```
浏览：`http://127.0.0.1:5173`

## 10 秒验证
后端跑起来后直接调用智能文生图管线（使用 Doubao Seedream，无密钥则返回占位图便于验证链路）：
```bash
curl -X POST http://127.0.0.1:8000/v1/pipeline/text2image \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a cozy japanese coffee shop interior, soft light",
    "providers": ["doubao_seedream"],
    "num_candidates": 1,
    "params": {"ratio": "1:1"}
  }'
```
在未配置密钥时，返回的 `best_image_url`/`candidates[*].url` 为 `data:` 开头的透明占位图；配置密钥后会返回真实图片。
