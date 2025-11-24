import { ComposeStage } from "../hooks/useImageCompose";
import type { ComposeStageValue } from "../hooks/useImageCompose";

const STAGES = [
  { stage: ComposeStage.Uploading, label: "上传图片", description: "载入参考图" },
  { stage: ComposeStage.Generating, label: "图像生成", description: "模型出图" },
  { stage: ComposeStage.Verifying, label: "一致性校验", description: "豆包判断主体一致" },
  { stage: ComposeStage.Completed, label: "完成", description: "输出营销图" },
];

interface ComposeTimelineProps {
  stage: ComposeStageValue;
}

export function ComposeTimeline({ stage }: ComposeTimelineProps) {
  if (stage === ComposeStage.Idle) {
    return null;
  }

  const stageIndex = STAGES.findIndex((item) => item.stage === stage);

  return (
    <div className="rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-400">
      <div className="mb-4 flex items-center justify-between">
        <span className="text-sm font-semibold text-white">生成进度</span>
        <span className="text-xs text-slate-500">
          {stage === ComposeStage.Completed ? "已完成" : "正在进行中"}
        </span>
      </div>
      <div className="relative flex items-center gap-3">
        <div className="absolute left-5 right-5 top-1/2 h-0.5 -translate-y-1/2 rounded-full bg-white/10" />
        <div
          className="absolute left-5 top-1/2 h-0.5 -translate-y-1/2 rounded-full bg-emerald-400/70 transition-all duration-500"
          style={{
            width: `calc((100% - 2.5rem) * ${
              stage === ComposeStage.Completed
                ? 1
                : Math.max(0, stageIndex) / (STAGES.length - 1 || 1)
            })`,
          }}
        />
        {STAGES.map((item, index) => {
          const isReached = stage >= item.stage;
          const isCurrent = stage === item.stage;
          return (
            <div key={item.stage} className="flex min-w-[120px] flex-1 flex-col items-center gap-2">
              <div
                className={`flex h-9 w-9 items-center justify-center rounded-full border transition ${
                  isReached
                    ? "border-emerald-400/70 bg-emerald-400/20 text-white"
                    : "border-white/20 bg-white/5 text-slate-400"
                } ${isCurrent ? "ring-4 ring-emerald-400/20" : ""}`}
              >
                <span className="text-sm">{index + 1}</span>
              </div>
              <div className="text-center text-xs text-slate-300">
                <div className={`font-medium ${isReached ? "text-white" : "text-slate-500"}`}>
                  {item.label}
                </div>
                <div className="mt-1 text-[11px] text-slate-500">{item.description}</div>
              </div>
              {index === stageIndex && stage !== ComposeStage.Completed && (
                <div className="mt-1 rounded-full bg-emerald-400/20 px-3 py-1 text-[10px] text-emerald-200">
                  处理中...
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
