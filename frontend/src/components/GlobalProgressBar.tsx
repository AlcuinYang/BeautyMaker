import { motion } from "framer-motion";

interface ProgressStep {
  label: string;
  description: string;
  icon: string;
}

interface GlobalProgressBarProps {
  steps: ProgressStep[];
  currentStep: number;
  status?: "idle" | "processing" | "success" | "error";
}

export function GlobalProgressBar({ steps, currentStep, status = "processing" }: GlobalProgressBarProps) {
  if (currentStep < 0) {
    return null;
  }

  const progressPercentage =
    status === "success" || currentStep >= steps.length - 1
      ? 1
      : Math.max(0, currentStep) / (steps.length - 1 || 1);

  return (
    <div className="rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-400">
      <div className="mb-4 flex items-center justify-between">
        <span className="text-sm font-semibold text-white">生成进度</span>
        <span className="text-xs text-slate-500">
          {status === "success" || currentStep >= steps.length - 1 ? "已完成" : "正在进行中"}
        </span>
      </div>
      <div className="relative flex items-center gap-3">
        {/* Background line */}
        <div className="absolute left-5 right-5 top-1/2 h-0.5 -translate-y-1/2 rounded-full bg-white/10" />

        {/* Animated progress line */}
        <motion.div
          className="absolute left-5 top-1/2 h-0.5 -translate-y-1/2 rounded-full bg-emerald-400/70"
          initial={{ width: 0 }}
          animate={{
            width: `calc((100% - 2.5rem) * ${progressPercentage})`,
          }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />

        {/* Step nodes */}
        {steps.map((step, index) => {
          const isReached = currentStep >= index;
          const isCurrent = currentStep === index;

          return (
            <motion.div
              key={`${step.label}-${index}`}
              className="flex min-w-[120px] flex-1 flex-col items-center gap-2"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1, duration: 0.3 }}
            >
              {/* Icon circle */}
              <motion.div
                className={`flex h-9 w-9 items-center justify-center rounded-full border transition-all ${
                  isReached
                    ? "border-emerald-400/70 bg-emerald-400/20 text-white"
                    : "border-white/20 bg-white/5 text-slate-400"
                } ${isCurrent ? "ring-4 ring-emerald-400/20" : ""}`}
                animate={
                  isCurrent
                    ? {
                        scale: [1, 1.1, 1],
                        transition: {
                          repeat: Infinity,
                          duration: 2,
                          ease: "easeInOut",
                        },
                      }
                    : { scale: 1 }
                }
              >
                <span className="text-base">{step.icon}</span>
              </motion.div>

              {/* Label and description */}
              <div className="text-center text-xs text-slate-300">
                <div className={`font-medium ${isReached ? "text-white" : "text-slate-500"}`}>
                  {step.label}
                </div>
                <div className="mt-1 text-[11px] text-slate-500">{step.description}</div>
              </div>

              {/* Processing indicator */}
              {isCurrent && status === "processing" && (
                <motion.div
                  className="mt-1 rounded-full bg-emerald-400/20 px-3 py-1 text-[10px] text-emerald-200"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  处理中...
                </motion.div>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
