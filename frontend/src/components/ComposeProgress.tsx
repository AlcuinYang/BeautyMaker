import { motion } from "framer-motion";
import { ComposeStage } from "../hooks/useImageCompose";
import type { ComposeStageValue } from "../hooks/useImageCompose";

const STAGES = [
  { stage: ComposeStage.Uploading, label: "上传图片", description: "载入参考图" },
  { stage: ComposeStage.Generating, label: "图像生成", description: "模型出图" },
  { stage: ComposeStage.Verifying, label: "一致性校验", description: "豆包判断主体一致" },
  { stage: ComposeStage.Completed, label: "完成", description: "输出营销图" },
];

interface ComposeProgressProps {
  stage: ComposeStageValue;
}

export function ComposeProgress({ stage }: ComposeProgressProps) {
  if (stage === ComposeStage.Idle) {
    return null;
  }

  const currentIndex = Math.max(
    0,
    STAGES.findIndex((item) => item.stage === stage),
  );

  const progressPercent = Math.min(
    100,
    Math.max(
      0,
      ((currentIndex + (stage === ComposeStage.Completed ? 1 : 0)) / STAGES.length) *
        100,
    ),
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="fixed bottom-6 left-1/2 z-30 w-[90%] max-w-3xl -translate-x-1/2 rounded-3xl border border-white/10 bg-black/40 p-4 text-xs text-slate-300 backdrop-blur-xl"
    >
      <div className="relative flex flex-wrap items-center gap-3">
        <div className="absolute left-6 right-6 top-6 h-0.5 rounded-full bg-white/10" />
        <div
          className="absolute left-6 top-6 h-0.5 rounded-full bg-emerald-400/70 transition-all duration-500"
          style={{ width: `calc((100% - 3rem) * ${progressPercent / 100})` }}
        />
        {STAGES.map((item) => {
          const isActive = stage >= item.stage;
          const isCurrent = stage === item.stage;
          return (
            <div
              key={item.stage}
              className={`relative flex min-w-[120px] flex-1 items-center gap-3 rounded-2xl px-3 py-3 transition ${
                isCurrent ? "bg-emerald-500/20 text-emerald-200" : ""
              }`}
            >
              <div
                className={`flex h-9 w-9 items-center justify-center rounded-full border text-sm ${
                  isActive
                    ? "border-emerald-400/60 bg-emerald-400/20 text-white"
                    : "border-white/20 bg-white/5 text-slate-400"
                }`}
              >
                {item.label.slice(0, 1)}
              </div>
              <div className="flex flex-col">
                <span className={`text-sm font-medium ${isActive ? "text-white" : "text-slate-500"}`}>
                  {item.label}
                </span>
                <span className="text-[11px] text-slate-500">{item.description}</span>
              </div>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
}
