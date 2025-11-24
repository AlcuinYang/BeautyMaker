import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import type {
  ApplicationTemplate,
  ModuleToggleOption,
} from "../types";

export type ParameterPanelSubmit = {
  prompt: string;
  outputCount: number;
  aspectRatio: string;
  promptMode: "direct" | "expand";
  selectedModules: string[];
  applyClarity: boolean;
  enableAesthetic: boolean;
};

type ParameterPanelProps = {
  template: ApplicationTemplate;
  moduleOptions: ModuleToggleOption[];
  isSubmitting: boolean;
  defaultPrompt?: string;
  errorMessage?: string | null;
  onRun: (values: ParameterPanelSubmit) => Promise<void> | void;
};

const ASPECT_RATIOS = [
  { label: "1 : 1", value: "1:1" },
  { label: "3 : 4", value: "3:4" },
  { label: "9 : 16", value: "9:16" },
];

const PROMPT_MODES: Array<{ label: string; value: "direct" | "expand"; hint: string }> = [
  {
    label: "直接输入",
    value: "direct",
    hint: "直接使用你的提示词进行生成。",
  },
  {
    label: "智能扩写",
    value: "expand",
    hint: "系统会自动扩写提示词以获得更细致的画面。",
  },
];

export function ParameterPanel({
  template,
  moduleOptions,
  isSubmitting,
  defaultPrompt,
  errorMessage,
  onRun,
}: ParameterPanelProps) {
  const defaultModules = useMemo(() => {
    if (moduleOptions.length === 0) return [];
    return moduleOptions.map((item) => item.key);
  }, [moduleOptions]);

  const [prompt, setPrompt] = useState(
    (defaultPrompt as string | undefined) ??
      (template.default_params?.prompt as string | undefined) ??
      "",
  );
  const [outputCount, setOutputCount] = useState(
    Number(template.default_params?.num_outputs ?? 1),
  );
  const [aspectRatio, setAspectRatio] = useState(
    (template.default_params?.aspect_ratio as string | undefined) ?? "1:1",
  );
  const [promptMode, setPromptMode] = useState<"direct" | "expand">("direct");
  const [selectedModules, setSelectedModules] =
    useState<string[]>(defaultModules);
  const [enableAesthetic, setEnableAesthetic] = useState(true);
  const [applyClarity, setApplyClarity] = useState(true);

  useEffect(() => {
    setPrompt(
      (defaultPrompt as string | undefined) ??
        (template.default_params?.prompt as string | undefined) ??
        "",
    );
    setOutputCount(Number(template.default_params?.num_outputs ?? 1));
    setAspectRatio(
      (template.default_params?.aspect_ratio as string | undefined) ?? "1:1",
    );
    setSelectedModules(defaultModules);
  }, [template, defaultPrompt, defaultModules]);

  const handleModuleToggle = (key: string) => {
    setSelectedModules((prev) =>
      prev.includes(key) ? prev.filter((item) => item !== key) : [...prev, key],
    );
  };

  const incrementCount = (delta: number) => {
    setOutputCount((current) => {
      const next = Math.min(4, Math.max(1, current + delta));
      return next;
    });
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onRun({
      prompt: prompt.trim(),
      outputCount,
      aspectRatio,
      promptMode,
      selectedModules,
      applyClarity,
      enableAesthetic,
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex h-full flex-col gap-6 rounded-3xl border border-white/10 bg-white/5 p-6 text-slate-200 backdrop-blur-xl"
    >
      <div className="space-y-5">
        <section className="space-y-3">
          <header className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
              生成配置
            </span>
            <span className="text-xs text-slate-500">
              输出张数最高 4 张
            </span>
          </header>

          <div className="rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-slate-200">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">输出数量</span>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  aria-label="减少数量"
                  onClick={() => incrementCount(-1)}
                  className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 text-lg leading-none text-slate-200 transition hover:bg-emerald-400/30"
                >
                  –
                </button>
                <span className="w-8 text-center text-base font-semibold text-emerald-200">
                  {outputCount}
                </span>
                <button
                  type="button"
                  aria-label="增加数量"
                  onClick={() => incrementCount(1)}
                  className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 text-lg leading-none text-slate-200 transition hover:bg-emerald-400/30"
                >
                  +
                </button>
              </div>
            </div>
          </div>

          <label className="flex flex-col gap-2 text-sm text-slate-300">
            <span className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
              画面比例
            </span>
            <select
              value={aspectRatio}
              onChange={(event) => setAspectRatio(event.target.value)}
              className="h-12 rounded-2xl border border-white/10 bg-black/30 px-4 text-sm text-white outline-none transition focus:border-emerald-400/60 focus:ring-2 focus:ring-emerald-400/30"
            >
              {ASPECT_RATIOS.map((ratio) => (
                <option key={ratio.value} value={ratio.value}>
                  {ratio.label}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-2 text-sm text-slate-300">
            <span className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
              文本输入方式
            </span>
            <div className="grid gap-3">
              {PROMPT_MODES.map((item) => (
                <button
                  type="button"
                  key={item.value}
                  onClick={() => setPromptMode(item.value)}
                  className={`rounded-2xl border px-4 py-3 text-left transition ${
                    promptMode === item.value
                      ? "border-emerald-400/70 bg-emerald-400/10 text-emerald-200"
                      : "border-white/10 bg-black/30 text-slate-300 hover:border-emerald-400/40 hover:bg-emerald-400/5"
                  }`}
                >
                  <div className="text-sm font-semibold">{item.label}</div>
                  <p className="mt-1 text-xs text-slate-400">{item.hint}</p>
                </button>
              ))}
            </div>
          </label>
        </section>

        <section className="space-y-3">
          <span className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
            提示词
          </span>
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="描述你想要的画面，例如：『清晨的雨后城市，霓虹反射在湿润的街面』"
            className="min-h-[160px] w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none transition focus:border-emerald-400/60 focus:ring-2 focus:ring-emerald-400/30"
          />
        </section>

        <section className="space-y-3">
          <header className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
              实验室模块
            </span>
            <button
              type="button"
              onClick={() =>
                setSelectedModules((prev) =>
                  prev.length === moduleOptions.length ? [] : defaultModules,
                )
              }
              className="text-xs text-emerald-300 transition hover:text-emerald-200"
            >
              {selectedModules.length === moduleOptions.length ? "全部取消" : "全选"}
            </button>
          </header>

          <div className="grid gap-3">
            {moduleOptions.map((module) => {
              const active = selectedModules.includes(module.key);
              return (
                <button
                  type="button"
                  key={module.key}
                  onClick={() => handleModuleToggle(module.key)}
                  className={`flex items-start justify-between rounded-2xl border px-4 py-3 text-left transition ${
                    active
                      ? "border-emerald-400/70 bg-emerald-400/10 text-emerald-100"
                      : "border-white/10 bg-black/30 text-slate-300 hover:border-emerald-400/40 hover:bg-emerald-400/5"
                  }`}
                >
                  <div>
                    <div className="text-sm font-semibold">{module.label}</div>
                    {module.description && (
                      <p className="mt-1 text-xs text-slate-400">
                        {module.description}
                      </p>
                    )}
                  </div>
                  <span
                    className={`mt-1 inline-flex h-4 w-4 items-center justify-center rounded-full border ${
                      active
                        ? "border-emerald-400 bg-emerald-400/40"
                        : "border-white/20"
                    }`}
                  >
                    {active ? "✓" : ""}
                  </span>
                </button>
              );
            })}
          </div>
        </section>

        <section className="space-y-3">
          <span className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
            增强选项
          </span>

          <div className="grid gap-3">
            <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-slate-300">
              <div>
                <div className="font-medium text-slate-200">美学增强</div>
                <p className="text-xs text-slate-500">
                  调用实验室评分模型生成美学指数。
                </p>
              </div>
              <input
                type="checkbox"
                checked={enableAesthetic}
                onChange={(event) => setEnableAesthetic(event.target.checked)}
                className="h-5 w-5 accent-emerald-400"
              />
            </label>

            <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-slate-300">
              <div>
                <div className="font-medium text-slate-200">图片清晰术</div>
                <p className="text-xs text-slate-500">
                  自动锐化细节与对比度，适合大图输出。
                </p>
              </div>
              <input
                type="checkbox"
                checked={applyClarity}
                onChange={(event) => setApplyClarity(event.target.checked)}
                className="h-5 w-5 accent-emerald-400"
              />
            </label>
          </div>
        </section>

        {errorMessage && (
          <div className="rounded-2xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-xs text-rose-200">
            {errorMessage}
          </div>
        )}
      </div>

      <motion.button
        type="submit"
        whileTap={{ scale: 0.98 }}
        disabled={isSubmitting}
        className="mt-auto inline-flex items-center justify-center rounded-full bg-gradient-to-r from-emerald-500 via-teal-500 to-sky-500 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/25 transition hover:from-emerald-400 hover:via-teal-400 hover:to-sky-400 disabled:cursor-not-allowed disabled:bg-slate-500 disabled:shadow-none"
      >
        {isSubmitting ? "正在运行..." : "运行生成任务"}
      </motion.button>
    </form>
  );
}
