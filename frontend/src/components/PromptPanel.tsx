import { motion } from "framer-motion";
import { useMemo, useState } from "react";
import type { ChangeEvent } from "react";
import type { ProviderInfo } from "../types";

interface PromptPanelProps {
  prompt: string;
  onPromptChange: (value: string) => void;
  referenceImages: string[];
  onReferenceUpload: (file: File) => void;
  onReferenceDrop?: (files: File[]) => void;
  onReferenceRemove: (index: number) => void;
  numCandidates: number;
  onNumCandidatesChange: (value: number) => void;
  ratio: string;
  onRatioChange: (value: string) => void;
  providers: ProviderInfo[];
  providerMap: Record<string, ProviderInfo>;
  providersLoading: boolean;
  selectedProviders: string[];
  onAddProvider: (id: string) => void;
  onRemoveProvider: (id: string) => void;
  aestheticModel: string;
  onAestheticModelChange: (id: string) => void;
  onSubmit: () => void;
  disabled: boolean;
}

const RATIOS = [
  { label: "1:1", value: "1:1", size: "2048x2048" },
  { label: "3:4", value: "3:4", size: "1728x2304" },
  { label: "4:3", value: "4:3", size: "2304x1728" },
  { label: "9:16", value: "9:16", size: "1440x2560" },
  { label: "16:9", value: "16:9", size: "2560x1440" },
] as const;

const AESTHETIC_MODELS = [
  { id: "mnet_v1", name: "MNet V1", description: "多维度美学评分模型" },
] as const;

type ToolKey = "ratio" | "providers" | "count" | "aesthetic";

export function PromptPanel({
  prompt,
  onPromptChange,
  referenceImages,
  onReferenceUpload,
  onReferenceRemove,
  numCandidates,
  onNumCandidatesChange,
  ratio,
  onRatioChange,
  providers,
  providerMap,
  providersLoading,
  selectedProviders,
  onAddProvider,
  onRemoveProvider,
  onSubmit,
  disabled,
  onReferenceDrop,
  aestheticModel,
  onAestheticModelChange,
}: PromptPanelProps) {
  const decrement = () => onNumCandidatesChange(Math.max(1, numCandidates - 1));
  const increment = () => onNumCandidatesChange(Math.min(6, numCandidates + 1));

  const handleReferenceFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onReferenceUpload(file);
    }
    event.target.value = "";
  };

  const [activeTool, setActiveTool] = useState<ToolKey | null>(null);
  const [selectedOption, setSelectedOption] = useState("");

  const providerOptions = useMemo(() => {
    return providers.filter((item) => item.is_active || selectedProviders.includes(item.id));
  }, [providers, selectedProviders]);

  const primaryProviderLabel = useMemo(() => {
    if (selectedProviders.length === 0) {
      return providersLoading ? "加载模型..." : "选择模型";
    }
    if (selectedProviders.length === 1) {
      return providerMap[selectedProviders[0]]?.display_name ?? selectedProviders[0];
    }
    return `已选 ${selectedProviders.length} 个模型`;
  }, [selectedProviders, providerMap, providersLoading]);

  const ratioSize = useMemo(() => {
    return RATIOS.find((item) => item.value === ratio)?.size ?? RATIOS[0].size;
  }, [ratio]);

  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="flex flex-col gap-5 rounded-3xl border border-white/10 bg-white/5 p-6 text-sm text-slate-200 backdrop-blur-xl"
    >
      <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
        <div className="space-y-3">
          <span className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
            提示词
          </span>
          <div
            className="relative"
            onDragOver={(event) => {
              if (disabled) return;
              event.preventDefault();
            }}
            onDrop={(event) => {
              if (disabled) return;
              event.preventDefault();
              const files = Array.from(event.dataTransfer.files || []);
              if (files.length && onReferenceDrop) {
                onReferenceDrop(files);
              }
            }}
          >
            <textarea
              value={prompt}
              onChange={(event) => onPromptChange(event.target.value)}
              placeholder="描述你想要的画面..."
              className="min-h-[220px] w-full rounded-2xl border border-white/10 bg-black/30 px-4 pb-4 pt-28 text-base text-white outline-none transition focus:border-emerald-400/60 focus:ring-2 focus:ring-emerald-400/30"
            />
            <div className="pointer-events-none absolute left-4 right-4 top-4 flex flex-wrap items-center gap-3">
              {referenceImages.map((image, index) => (
                <div
                  key={index}
                  className="pointer-events-auto relative flex h-16 w-16 items-center justify-center overflow-hidden rounded-2xl border border-white/10 bg-black/40 shadow-lg shadow-black/30"
                >
                  <img src={image} alt={`参考图片 ${index + 1}`} className="h-full w-full object-cover" />
                  <button
                    type="button"
                    onClick={(event) => {
                      event.preventDefault();
                      onReferenceRemove(index);
                    }}
                    className="absolute -right-1 -top-1 inline-flex h-5 w-5 items-center justify-center rounded-full border border-white/20 bg-black/70 text-xs text-white transition hover:border-emerald-400/50 hover:bg-emerald-400/30"
                  >
                    ×
                  </button>
                </div>
              ))}
              {referenceImages.length < 10 && (
                <label className="pointer-events-auto flex h-16 w-16 cursor-pointer flex-col items-center justify-center gap-1 rounded-2xl border border-dashed border-white/15 bg-black/30 text-slate-400 transition hover:border-emerald-400/60 hover:text-emerald-200">
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={handleReferenceFileChange}
                    disabled={disabled}
                  />
                  <PlusImageIcon />
                  <span className="text-[10px] text-slate-500">
                    {referenceImages.length > 0 ? `${referenceImages.length}/10` : "添加"}
                  </span>
                </label>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <ToolButton
          icon="🎛️"
          label={`比例 ${ratio}`}
          active={activeTool === "ratio"}
          onClick={() => setActiveTool((current) => (current === "ratio" ? null : "ratio"))}
          disabled={disabled}
        />
        <ToolButton
          icon="🧠"
          label={primaryProviderLabel}
          active={activeTool === "providers"}
          onClick={() => setActiveTool((current) => (current === "providers" ? null : "providers"))}
          disabled={providersLoading && selectedProviders.length === 0}
        />
        <ToolButton
          icon="🖼️"
          label={`输出 ${numCandidates} 张`}
          active={activeTool === "count"}
          onClick={() => setActiveTool((current) => (current === "count" ? null : "count"))}
          disabled={disabled}
        />
        <ToolButton
          icon="⚡"
          label="美学评分"
          active={activeTool === "aesthetic"}
          onClick={() => setActiveTool((current) => (current === "aesthetic" ? null : "aesthetic"))}
          disabled={disabled}
        />
        {/* <ToolButton icon="✨" label="扩写已关闭" active={false} disabled /> */}
      </div>

      {activeTool === "ratio" && (
        <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-slate-200">
          <label className="flex items-center gap-3">
            <span className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
              画面比例
            </span>
            <select
              value={ratio}
              onChange={(event) => onRatioChange(event.target.value)}
              disabled={disabled}
              className="h-11 rounded-xl border border-white/10 bg-black/30 px-4 text-sm text-white outline-none transition focus:border-emerald-400/60 focus:ring-2 focus:ring-emerald-400/30 disabled:cursor-not-allowed disabled:text-slate-500"
            >
              {RATIOS.map((item) => (
                <option key={item.value} value={item.value}>
                  {`${item.label} (${item.size})`}
                </option>
              ))}
            </select>
          </label>
          <span className="text-xs text-slate-500">输出分辨率：{ratioSize}</span>
        </div>
      )}

      {activeTool === "providers" && (
        <div className="space-y-3 rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-slate-200">
          <label className="flex items-center gap-3">
            <span className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
              新增模型
            </span>
            <select
              value={selectedOption}
              onChange={(event) => {
                const value = event.target.value;
                if (!value) return;
                setSelectedOption("");
                onAddProvider(value);
              }}
              disabled={providersLoading || providerOptions.length === 0}
              className="h-11 flex-1 rounded-xl border border-white/10 bg-black/30 px-4 text-sm text-white outline-none transition focus:border-emerald-400/60 focus:ring-2 focus:ring-emerald-400/30 disabled:cursor-not-allowed disabled:text-slate-500"
            >
              <option value="">
                {providerOptions.length === 0
                  ? providersLoading
                    ? "正在加载..."
                    : "暂无可用模型"
                  : "请选择模型"}
              </option>
              {providerOptions
                .filter((item) => !selectedProviders.includes(item.id))
                .map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.display_name}
                  </option>
                ))}
            </select>
          </label>

          {selectedProviders.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {selectedProviders.map((id) => {
                const info = providerMap[id];
                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => onRemoveProvider(id)}
                    className="inline-flex items-center gap-2 rounded-full border border-emerald-300/40 bg-emerald-400/10 px-3 py-1 text-xs text-emerald-100 transition hover:border-emerald-400/70 hover:bg-emerald-400/20"
                  >
                    <span>{info?.display_name ?? id}</span>
                    <span className="rounded-full bg-emerald-400/30 px-1.5 text-[10px] text-emerald-900">
                      移除
                    </span>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-white/15 bg-black/30 px-3 py-2 text-xs text-slate-500">
              请选择至少一个模型开始生成。
            </div>
          )}

          {providerOptions.length > 0 && (
            <div className="flex flex-wrap gap-3 text-[11px] text-slate-500">
              {providerOptions.map((item) => (
                <span
                  key={item.id}
                  className={`inline-flex items-center gap-1 rounded-full border px-3 py-1 ${
                    selectedProviders.includes(item.id)
                      ? "border-emerald-300/60 bg-emerald-400/10 text-emerald-100"
                      : "border-white/10 bg-black/40 text-slate-400"
                  }`}
                >
                  {item.display_name}
                  {item.is_free && <span className="text-[10px] text-emerald-200">FREE</span>}
                </span>
              ))}
            </div>
          )}

          <p className="text-xs text-slate-500">
            同时启用多个模型，可并行生成候选图并自动评分排序。
          </p>
        </div>
      )}

      {activeTool === "count" && (
        <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-slate-200">
          <div className="space-y-1">
            <span className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
              输出数量
            </span>
            <p className="text-xs text-slate-500">单次最多 6 张，可重复生成挑选。</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={decrement}
              disabled={disabled}
              className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-lg leading-none text-white transition hover:bg-emerald-400/30 disabled:cursor-not-allowed disabled:bg-white/5"
            >
              –
            </button>
            <span className="w-10 text-center text-lg font-semibold text-emerald-200">
              {numCandidates}
            </span>
            <button
              type="button"
              onClick={increment}
              disabled={disabled}
              className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-lg leading-none text-white transition hover:bg-emerald-400/30 disabled:cursor-not-allowed disabled:bg-white/5"
            >
              +
            </button>
          </div>
        </div>
      )}

      {activeTool === "aesthetic" && (
        <div className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-slate-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
              美学评分模型
            </span>
            <div className="flex items-center gap-2 rounded-lg border border-emerald-400/30 bg-emerald-400/10 px-3 py-1">
              <span className="text-xs text-emerald-300">⚡</span>
              <span className="text-xs font-medium text-emerald-200">已启用</span>
            </div>
          </div>
          <div className="space-y-2">
            {AESTHETIC_MODELS.map((model) => (
              <button
                key={model.id}
                type="button"
                onClick={() => onAestheticModelChange(model.id)}
                disabled={disabled}
                className={`w-full rounded-lg border p-3 text-left transition ${
                  aestheticModel === model.id
                    ? "border-emerald-400/60 bg-emerald-400/10"
                    : "border-white/10 bg-white/5 hover:border-emerald-400/40 hover:bg-white/10"
                } disabled:cursor-not-allowed disabled:opacity-50`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-white">{model.name}</span>
                      {aestheticModel === model.id && (
                        <span className="rounded-full bg-emerald-400/20 px-2 py-0.5 text-[10px] font-medium text-emerald-200">
                          当前
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-slate-400">{model.description}</p>
                  </div>
                  {aestheticModel === model.id && (
                    <svg
                      className="h-5 w-5 text-emerald-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </div>
              </button>
            ))}
          </div>
          <p className="text-xs text-slate-500">
            调用实验室评分模型生成美学指数。
          </p>
        </div>
      )}

      {/* Prompt expansion disabled pending better implementation */}

      <motion.button
        type="button"
        onClick={onSubmit}
        whileTap={{ scale: disabled ? 1 : 0.98 }}
        disabled={disabled}
        className="mt-1 inline-flex items-center justify-center rounded-full bg-gradient-to-r from-emerald-500 via-teal-500 to-sky-500 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/25 transition hover:from-emerald-400 hover:via-teal-400 hover:to-sky-400 disabled:cursor-not-allowed disabled:bg-slate-600 disabled:shadow-none"
      >
        {disabled ? "正在生成..." : "生成最美图片"}
      </motion.button>
    </motion.div>
  );
}

interface ToolButtonProps {
  icon: string;
  label: string;
  active: boolean;
  disabled?: boolean;
  onClick: () => void;
}

function ToolButton({ icon, label, active, disabled = false, onClick }: ToolButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex items-center gap-2 rounded-2xl border px-3 py-2 text-xs transition ${
        active
          ? "border-emerald-400/70 bg-emerald-400/10 text-emerald-100 shadow-lg shadow-emerald-500/20"
          : "border-white/10 bg-black/30 text-slate-300 hover:border-emerald-400/40 hover:bg-black/40"
      } disabled:cursor-not-allowed disabled:opacity-60`}
    >
      <span className="text-base leading-none">{icon}</span>
      <span>{label}</span>
    </button>
  );
}

function PlusImageIcon() {
  return (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="text-slate-400"
    >
      <rect x="3" y="3" width="18" height="18" rx="4" strokeDasharray="4 3" />
      <path d="M12 8v8" />
      <path d="M8 12h8" />
    </svg>
  );
}
