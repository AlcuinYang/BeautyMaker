# 管线使用指南

**如何选择合适的 Pipeline？**

---

## 📊 两个 Pipeline 对比

| 特性 | Text2Image Pipeline | Image2Image Pipeline |
|------|-------------------|---------------------|
| **API 端点** | `POST /v1/pipeline/text2image` | `POST /v1/pipeline/image2image` |
| **主要用途** | 通用图像创意生成 | 电商营销图生成 |
| **参考图作用** | 风格参考、内容启发 | **产品主体一致性保持** |
| **目标用户** | 设计师、艺术创作者 | 电商运营、营销人员 |

---

## 🎨 Text2Image Pipeline（通用创意工具）

### 适用场景

✅ **风格迁移** - 参考某种艺术风格生成新图像
```json
{
  "prompt": "一只猫咪",
  "reference_images": ["梵高的星空.jpg"],
  "providers": ["doubao_seedream"]
}
```

✅ **创意灵感** - 基于参考图创作新内容
```json
{
  "prompt": "未来科技城市",
  "reference_images": ["赛博朋克风格图.jpg"],
  "providers": ["qwen"]
}
```

✅ **多图融合** - 融合多张参考图的元素
```json
{
  "prompt": "融合两种风格",
  "reference_images": ["风格A.jpg", "风格B.jpg"],
  "providers": ["doubao_seedream"]
}
```

### 核心特点

- 🎯 **灵活自由** - 不强制保持主体一致性
- 🚀 **快速简单** - 无复杂的电商业务逻辑
- 🎨 **创意优先** - 专注于艺术表现和风格
- 📊 **美学评分** - 提供 6 维度专业评分

### 工作流程

```
用户输入 Prompt + 参考图
    ↓
多提供商并行生成（自动切换 i2i 模型）
    ↓
豆包 Vision 美学评分（6 维度）
    ↓
智能选择最佳候选
    ↓
返回结果 + 评分 + 点评
```

---

## 🛍️ Image2Image Pipeline（电商营销专用）

### 适用场景

✅ **产品营销图** - 保持产品主体，改变背景和氛围
```json
{
  "prompt": "清新自然的营销风格",
  "reference_images": ["口红产品原图.jpg"],
  "providers": ["qwen", "doubao_seedream"],
  "params": {
    "platform": "淘宝",
    "product": "化妆品",
    "style": "清新"
  }
}
```

✅ **电商海报** - 生成符合平台规范的营销素材
```json
{
  "prompt": "618大促海报",
  "reference_images": ["产品图1.jpg", "产品图2.jpg"],
  "params": {
    "platform": "京东",
    "use_prompt_bank": true
  }
}
```

### 核心特点

- 🎯 **主体一致** - 豆包 Vision 一致性检测（确保是同一产品）
- 📚 **Prompt 模板库** - 营销文案自动融合
- 🏪 **平台优化** - 淘宝/京东等平台特定参数
- 🔄 **在线学习** - 根据评分更新模板权重
- 📝 **完整日志** - 记录所有决策过程

### 工作流程

```
用户上传产品图 + 营销需求
    ↓
豆包 Vision 分析参考图（产品类别/风格/关键词）
    ↓
Prompt 模板库检索和融合
    ↓
多提供商并行生成
    ↓
豆包美学评分（6 维度）
    ↓
一致性检测（参考图 vs 生成图，0-1 分）
    ↓
综合排序（美学分 + 一致性分）
    ↓
美学反馈机制（更新模板权重）
    ↓
返回结果 + 事件日志
```

---

## 🤔 如何选择？

### 选择 Text2Image 如果：

- ✅ 你想要**艺术创作**、风格迁移
- ✅ 参考图只是**灵感来源**，不需要保持主体
- ✅ 你需要**快速生成**，不需要复杂逻辑
- ✅ 你在做设计、插画、艺术项目

**示例：**
> "我看到一张赛博朋克风格的图，想生成类似风格的猫咪"

---

### 选择 Image2Image 如果：

- ✅ 你在做**电商营销**，需要产品图
- ✅ 参考图是**产品原图**，生成图必须是同一产品
- ✅ 你需要**一致性保证**（主体不能变）
- ✅ 你需要**营销模板库**和平台优化

**示例：**
> "我有一张口红产品图，想生成淘宝营销海报，但必须是同一支口红"

---

## 💡 特殊情况

### 我想要风格迁移 + 主体保持？

**推荐：Image2Image Pipeline**

因为它有一致性检测，可以确保主体不变。

---

### 我只是想试试效果，不在意主体是否一致？

**推荐：Text2Image Pipeline**

更简单快速，适合快速实验。

---

## 📝 API 参数对比

### Text2Image

```json
{
  "prompt": "描述想要的效果",
  "providers": ["doubao_seedream", "qwen"],
  "num_candidates": 3,
  "reference_images": ["url1", "url2"],  // 可选，1-10张
  "params": {
    "ratio": "16:9",
    "modules": ["holistic", "color_score", ...]
  }
}
```

### Image2Image

```json
{
  "prompt": "营销需求描述",
  "reference_images": ["产品原图.jpg"],  // 必需
  "providers": ["qwen", "doubao_seedream"],
  "params": {
    "platform": "淘宝",      // 可选
    "product": "化妆品",     // 可选
    "style": "清新",         // 可选
    "use_prompt_bank": true, // 是否使用模板库
    "num_variations": 2      // 变体数量
  }
}
```

---

## 🎯 实战建议

### 场景 1：设计师做插画

```
需求：参考莫奈的画风，画一只猫
Pipeline：Text2Image ✅
理由：不需要保持主体一致，只要风格像就行
```

### 场景 2：电商运营做营销图

```
需求：产品口红不变，换个营销背景
Pipeline：Image2Image ✅
理由：必须确保是同一支口红（一致性检测）
```

### 场景 3：快速试验 AI 绘画

```
需求：上传一张图，看看能生成什么
Pipeline：Text2Image ✅
理由：简单快速，适合实验
```

---

## 📚 延伸阅读

- [完整项目文档](./项目完整文档.md)
- [API 接口文档](./项目完整文档.md#api接口文档)
- [提供商文档](./seedreamAPI.md)
