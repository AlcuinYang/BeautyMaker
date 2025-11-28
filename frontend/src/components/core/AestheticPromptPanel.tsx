import { useMemo, type ChangeEvent } from "react";
import { motion } from "framer-motion";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { Input } from "../ui/Input";
import { RATIO_OPTIONS } from "../registry/aestheticOptions";

type AestheticPromptPanelProps = {
  prompt: string;
  onPromptChange: (value: string) => void;
  ratio: string;
  onRatioChange: (value: string) => void;
  count: number;
  onCountChange: (value: number) => void;
  onRun: () => void;
  isRunning: boolean;
};

export function AestheticPromptPanel({
  prompt,
  onPromptChange,
  ratio,
  onRatioChange,
  count,
  onCountChange,
  onRun,
  isRunning,
}: AestheticPromptPanelProps) {
  const handleTextareaChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    onPromptChange(event.target.value);
  };

  const handleCountChange = (event: ChangeEvent<HTMLInputElement>) => {
    const next = Number.parseInt(event.target.value, 10);
    if (Number.isNaN(next)) return;
    onCountChange(Math.min(8, Math.max(1, next)));
  };

  const sizeLabel = useMemo(() => {
    const preset = RATIO_OPTIONS.find((option) => option.value === ratio);
    if (!preset) return "1024 × 1024";
    if (preset.value === "1:1") return "1024 × 1024";
    if (preset.value === "3:4") return "1024 × 1365";
    if (preset.value === "9:16") return "1024 × 1820";
    return (preset as { value: string; label: string }).label;
  }, [ratio]);

  return (
    <motion.div
      initial={{ opacity: 0, x: -40 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="flex h-full flex-col gap-6 overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-6 text-slate-200 backdrop-blur-xl"
    >
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-white">人物模特 · 智能提示</h2>
            <p className="mt-1 text-sm text-slate-400">
              参考 RunningHub.ai 的操作体验，快速生成多风格人物样张。
            </p>
          </div>
          <div className="flex flex-col items-end text-xs text-slate-400">
            <span className="rounded-full border border-white/10 bg-black/40 px-3 py-1 font-medium uppercase tracking-[0.3em]">
              Prompt Engine
            </span>
            <span className="mt-2 flex items-center gap-4 text-slate-500">
              ❤ 5.1K · 🔁 268 · 评论 84
            </span>
          </div>
        </div>
        <Card className="space-y-2 bg-black/30">
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase tracking-[0.3em] text-slate-400">提示词</span>
            <button
              type="button"
              className="text-xs text-emerald-300 transition hover:text-emerald-200"
            >
              一键填充示例
            </button>
          </div>
          <textarea
            value={prompt}
            onChange={handleTextareaChange}
            placeholder="描述你的模特、风格、光效等细节..."
            className="h-56 w-full resize-none rounded-2xl border border-white/10 bg-black/40 px-4 py-3 text-sm leading-relaxed text-white outline-none transition focus:border-emerald-400/60 focus:ring-2 focus:ring-emerald-400/30"
          />
          <p className="text-xs text-slate-500">
            建议描述人物妆发、服装质感、姿势与环境氛围，精准控制生成效果。
          </p>
        </Card>
      </div>

      <div className="space-y-4 rounded-3xl border border-white/10 bg-black/25 p-5 text-sm text-slate-200">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.3em] text-slate-400">图像比例</label>
            <div className="flex gap-2">
              {RATIO_OPTIONS.map((option) => {
                const active = option.value === ratio;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => onRatioChange(option.value)}
                    className={`w-full rounded-2xl border px-3 py-2 text-xs transition ${
                      active
                        ? "border-emerald-400/70 bg-emerald-400/10 text-emerald-100"
                        : "border-white/10 bg-white/5 text-slate-300 hover:border-emerald-400/40"
                    }`}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.3em] text-slate-400">
              输出尺寸（参考）
            </label>
            <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-xs text-slate-300">
              {sizeLabel}
            </div>
            <p className="text-xs text-slate-500">尺寸与所选模型适配，可在运行后放大。</p>
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-xs uppercase tracking-[0.3em] text-slate-400">批次数量</label>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => onCountChange(Math.max(1, count - 1))}
              className="flex h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-white/5 text-lg text-white transition hover:border-emerald-400/50 hover:bg-emerald-400/10"
              disabled={isRunning}
            >
              –
            </button>
            <Input
              type="number"
              min={1}
              max={8}
              value={count}
              onChange={handleCountChange}
              className="h-9 w-20 text-center"
              disabled={isRunning}
            />
            <button
              type="button"
              onClick={() => onCountChange(Math.min(8, count + 1))}
              className="flex h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-white/5 text-lg text-white transition hover:border-emerald-400/50 hover:bg-emerald-400/10"
              disabled={isRunning}
            >
              +
            </button>
          </div>
          <p className="text-xs text-slate-500">建议 1-4 张用于精挑细选。</p>
        </div>

        <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-xs text-slate-400">
          <span>模型兼容：Qwen · Doubao · Nano Banana</span>
          <span className="text-emerald-200">自动匹配最佳分辨率</span>
        </div>
      </div>

      <div className="flex items-center justify-between gap-4">
        <div className="hidden text-xs text-slate-500 md:flex">
          <span>Shift + Enter 快速运行 · 模型兼容度自动匹配</span>
        </div>
        <div className="flex items-center gap-3">
          <Button type="button" variant="secondary" disabled={isRunning} className="px-5">
            分享有礼
          </Button>
          <Button type="button" onClick={onRun} disabled={isRunning} className="px-8 py-3 text-base">
            {isRunning ? "运行中..." : "运行 (Run)"}
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
