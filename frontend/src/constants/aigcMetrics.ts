export const AIGC_METRIC_LABELS: Record<string, string> = {
  quality_score: "语义忠实度",
  clarity_eval: "结构合理性",
  contrast_score: "物理逻辑",
  noise_eval: "画面纯净度",
  color_score: "艺术美感",
  holistic: "综合评分",
};

export const AIGC_METRIC_ORDER: string[] = [
  "quality_score",
  "clarity_eval",
  "contrast_score",
  "noise_eval",
  "color_score",
  "holistic",
];
