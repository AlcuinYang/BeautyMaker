# Comparative Review Feature Implementation

## Overview
This document describes the implementation of the "Funnel Comparative Review" feature for the Text2ImagePipeline. This feature automatically generates a qualitative explanation of why the best-scoring image was selected over the lowest-scoring one, using evidence-based reasoning backed by quantitative scores.

## Architecture

### 1. Doubao Client Extension
**File**: `services/scoring/holistic/doubao_client.py`

Added a new `compare_images` method to the `DoubaoAestheticClient` class that:
- Accepts multiple image URLs and a comparison prompt
- Constructs multi-image vision API requests
- Enforces strict JSON output format
- Includes robust fallback mechanism when API is unavailable

**Key Features**:
- Multi-image input support
- Structured JSON response (`title`, `analysis`, `key_difference`)
- Graceful degradation with fallback response
- Proper error handling and logging

### 2. Pipeline Integration
**File**: `services/pipeline/text2image.py`

#### New Function: `_generate_comparative_review`
This async helper function:
- Formats scores on a 0-10 scale for better readability
- Constructs an evidence-based prompt that includes:
  - Winner's scores across all dimensions
  - Loser's scores across all dimensions
  - Specific instructions for comparative analysis
- Handles None values in scores gracefully
- Returns None on failure (optional field in response)

#### Modified: `run_text2image_pipeline`
Enhanced the main pipeline function to:
- Check if multiple candidates exist (`len(candidates) > 1`)
- Identify the "loser" (lowest composite score) for comparison
- Generate comparative review using Doubao Vision API
- Include review in response only when available

**Edge Cases Handled**:
- Single candidate: No review generated (nothing to compare)
- Missing evaluations: Review skipped
- API failure: Graceful fallback, review is None
- Missing scores: Formatted as "0.0/10"

### 3. Response Schema
**File**: `services/pipeline/text2image.py`

Added new Pydantic models:

#### `ComparativeReview`
```python
class ComparativeReview(BaseModel):
    title: str          # 4-8 character Chinese title
    analysis: str       # ~100 character comparative analysis
    key_difference: str # 1-2 key difference keywords
```

#### `Text2ImagePipelineResponse`
Extended the response model to include:
- `review: Optional[ComparativeReview]` - Only present when multiple candidates exist and comparison succeeds
- All existing fields remain unchanged
- Fully backward compatible

## Prompt Engineering

### Evidence-Based Reasoning
The comparative prompt includes:
1. **Quantitative Evidence**: All relevant scores for both images
2. **Clear Task**: Attribution analysis, deficiency identification, summary
3. **Structured Output**: Enforced JSON format

### Example Prompt Structure
```
请对比分析以下两张图片:

【图片 A（优胜图）】
- 综合评分：8.5/10
- 构图得分：9.0/10
- 光影得分：8.8/10
- 细节/清晰度：8.2/10

【图片 B（参照图）】
- 综合评分：6.5/10
- 构图得分：6.8/10
- 光影得分：7.0/10
- 细节/清晰度：6.0/10

【任务要求】
请根据上述评分差异，生成一段约 100 字的【对比点评】。
1. **归因分析**：直接指出图片 A 在哪些具体维度上胜过了图片 B。引用分数作为证据。
2. **缺陷指出**：温和指出图片 B 的主要败笔。
3. **总结**：一句话总结 A 的获胜理由。

【输出格式】
严格 JSON：
{
    "title": "胜出理由：[4-8字短标题]",
    "analysis": "[对比分析内容]",
    "key_difference": "[1-2个核心差异点关键词]"
}
```

## API Response Example

### Success Response (with review)
```json
{
  "status": "success",
  "task_id": "uuid-here",
  "best_image_url": "https://...",
  "best_composite_score": 0.85,
  "candidates": [...],
  "summary": "该图片在构图表达、光色表现等维度表现突出。",
  "prompt": {...},
  "providers_used": ["seedream_4_0"],
  "review": {
    "title": "胜出理由：构图与光影双优",
    "analysis": "图片 A 在构图得分(9.0分)和光影得分(8.8分)上明显领先图片 B(6.8分和7.0分)，展现了更稳定的视觉层次和柔和的光色过渡。图片 B 在细节清晰度上表现不足(6.0分)，导致整体观感略显模糊。图片 A 凭借其在构图稳定性和光影层次感上的优势脱颖而出。",
    "key_difference": "构图稳定、光影柔和"
  }
}
```

### Single Candidate Response (no review)
```json
{
  "status": "success",
  "task_id": "uuid-here",
  "best_image_url": "https://...",
  "best_composite_score": 0.85,
  "candidates": [{"image_url": "...", "provider": "...", "scores": {...}}],
  "summary": "该图片在构图表达、光色表现等维度表现突出。",
  "prompt": {...},
  "providers_used": ["seedream_4_0"]
}
```

## Testing

### Test File
`tests/test_comparative_review.py`

### Test Coverage
- ✅ Comparative review generation with mock data
- ✅ Fallback mechanism when API is disabled
- ✅ None score handling
- ✅ Proper formatting of scores
- ✅ Graceful error handling

### Run Tests
```bash
python tests/test_comparative_review.py
```

## Robustness Features

1. **Graceful Degradation**: If Doubao API is unavailable, the pipeline continues without the review field
2. **Null Safety**: All score accesses use `.get()` and None coalescing
3. **Multiple Fallbacks**: Client-level fallback → Pipeline-level None check → Optional field in response
4. **Backward Compatibility**: Existing clients see no breaking changes; review is an optional field

## Performance Considerations

- Review generation adds one additional API call to Doubao Vision
- Only triggered when `len(candidates) > 1`
- Runs after selection, does not block candidate generation
- Timeout: 30 seconds (inherited from DoubaoAestheticClient)

## Future Enhancements

1. **Caching**: Cache reviews for similar score patterns
2. **Multi-language**: Support English comparative reviews
3. **Top-N Comparison**: Compare best vs top-N instead of just lowest
4. **Score Delta Threshold**: Only generate review if score difference exceeds threshold
5. **User Control**: Add optional parameter to enable/disable review generation

## Files Modified

1. `services/scoring/holistic/doubao_client.py` - Added `compare_images` method
2. `services/pipeline/text2image.py` - Added review logic and response models
3. `services/pipeline/__init__.py` - Exported new response models
4. `tests/test_comparative_review.py` - New test file

## Dependencies

No new dependencies required. Uses existing:
- `httpx` for async HTTP requests
- `pydantic` for data validation
- Doubao Vision API (ARK_API_KEY or DOUBAO_API_KEY environment variable)
