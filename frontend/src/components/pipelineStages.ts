import { PipelineStage } from "../hooks/usePipeline";
import type { PipelineStageValue } from "../hooks/usePipeline";

export const STAGES: Array<{
  stage: PipelineStageValue;
  label: string;
  description: string;
  icon: string;
}> = [
  { stage: PipelineStage.ExpandingPrompt, label: "Prompt 扩写", description: "优化提示词", icon: "🟢" },
  { stage: PipelineStage.Generating, label: "图像生成", description: "模型出图", icon: "🔵" },
  { stage: PipelineStage.Scoring, label: "美学评分", description: "实验室打分", icon: "🟣" },
  { stage: PipelineStage.Completed, label: "完成", description: "挑出最美作品", icon: "✨" },
];
