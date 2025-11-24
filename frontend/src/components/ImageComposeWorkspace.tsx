import { useEffect, useMemo, useState, useCallback, useRef } from "react";
import type { ChangeEvent } from "react";
import { motion } from "framer-motion";
import { api } from "../lib/api";
import type { ImageComposeResponse, ImageComposeResultItem, ProviderInfo } from "../types";
import { useImageCompose, ComposeStage } from "../hooks/useImageCompose";
import type { ComposeStageValue } from "../hooks/useImageCompose";
import { ComposeTimeline } from "./ComposeTimeline";
import { ImagePreviewModal } from "./ImagePreviewModal";

const RATIO_OPTIONS = [
  { value: "1:1", label: "1 : 1", size: "2048x2048" },
  { value: "3:4", label: "3 : 4", size: "1728x2304" },
  { value: "4:3", label: "4 : 3", size: "2304x1728" },
  { value: "9:16", label: "9 : 16", size: "1440x2560" },
  { value: "16:9", label: "16 : 9", size: "2560x1440" },
] as const;

const RATIO_SIZE_MAP = RATIO_OPTIONS.reduce<Record<string, string>>((acc, item) => {
  acc[item.value] = item.size;
  return acc;
}, {});

const DEFAULT_RATIO = "1:1";

const PROVIDER_WHITELIST = new Set(["qwen", "doubao_seedream", "dalle", "nano_banana"]);

type ToolKey = "ratio" | "model" | "count";

export function ImageComposeWorkspace() {
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [providersLoading, setProvidersLoading] = useState(true);
  const [selectedProviders, setSelectedProviders] = useState<string[]>([]);
  const [prompt, setPrompt] = useState("为产品生成高转化电商宣传图");
  const [ratio, setRatio] = useState<string>(DEFAULT_RATIO);
  const [numVariations, setNumVariations] = useState(1);
  const [referenceImages, setReferenceImages] = useState<string[]>([]);
  const [referenceImageSizes, setReferenceImageSizes] = useState<number[]>([]);
  const [selectedUrls, setSelectedUrls] = useState<string[]>([]);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [groupMode, setGroupMode] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [activeTool, setActiveTool] = useState<ToolKey | null>(null);

  const { stage, result, error, isRunning, run, reset } = useImageCompose();

  useEffect(() => {
    let mounted = true;
    let storedProviders: string[] = [];

    if (typeof window !== "undefined") {
      const stored = window.localStorage.getItem("ae_compose_selected_providers");
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          if (Array.isArray(parsed)) {
            storedProviders = parsed.filter((item): item is string => typeof item === "string");
          }
        } catch (parseError) {
          console.warn("读取缓存的模型选择失败", parseError);
        }
      }
    }

    setProvidersLoading(true);
    api
      .listProviders()
      .then((data) => {
        if (!mounted) return;
        const filtered = data.filter((item) => PROVIDER_WHITELIST.has(item.id));

        if (!filtered.some((item) => item.id === "doubao_seedream")) {
          filtered.push({
            id: "doubao_seedream",
            display_name: "豆包 · Seedream",
            description: "豆包大模型 Seedream 文生图",
            category: "image_generation",
            is_free: false,
            is_active: true,
            icon: null,
            endpoint: "https://www.doubao.com/seeds/dream",
            latency_ms: null,
          });
        }

        setProviders(filtered);

        const validStored = storedProviders.find((id) =>
          filtered.some((item) => item.id === id),
        );
        const doubao = filtered.find((item) => item.id === "doubao_seedream");
        const fallback = filtered[0];
        const initial = validStored ?? doubao?.id ?? fallback?.id;
        setSelectedProviders(initial ? [initial] : []);
      })
      .catch((err) => console.error("加载模型列表失败", err))
      .finally(() => {
        if (mounted) {
          setProvidersLoading(false);
        }
      });
    return () => {
      mounted = false;
    };
  }, []);

  const providerMap = useMemo(() => {
    const map: Record<string, ProviderInfo> = {};
    providers.forEach((item) => {
      map[item.id] = item;
    });
    return map;
  }, [providers]);

  const providerOptions = useMemo(() => {
    return providers.filter((item) => item.is_active || selectedProviders.includes(item.id));
  }, [providers, selectedProviders]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(
        "ae_compose_selected_providers",
        JSON.stringify(selectedProviders),
      );
    }
  }, [selectedProviders]);

  const primaryProviderRef = useRef<string | undefined>(selectedProviders[0]);

  useEffect(() => {
    const primary = selectedProviders[0];
    const prev = primaryProviderRef.current;
    if (primary !== prev) {
      if (primary !== "doubao_seedream" && groupMode) {
        setGroupMode(false);
      }
      primaryProviderRef.current = primary;
    }
  }, [selectedProviders, groupMode]);

  useEffect(() => {
    setNumVariations((prev) => {
      const min = groupMode ? 2 : 1;
      const max = groupMode ? 15 : 3;
      return Math.min(Math.max(prev, min), max);
    });
  }, [groupMode]);

  const handleSelectProvider = useCallback((value: string) => {
    if (!value) return;
    setSelectedProviders([value]);
    setActiveTool(null);
  }, []);

  const handleRatioChange = useCallback((value: string) => {
    setRatio(value);
    setActiveTool(null);
  }, []);

  const handleModelChange = useCallback(
    (value: string) => {
      if (!value) return;
      setSelectedProviders([value]);
      setActiveTool(null);
    },
    [],
  );

  const handleCountChange = useCallback(
    (value: number) => {
      const min = groupMode ? 2 : 1;
      const max = groupMode ? 15 : 3;
      const clamped = Math.min(Math.max(value, min), max);
      setNumVariations(clamped);
      setActiveTool(null);
    },
    [groupMode],
  );

  const handleGenerate = () => {
    if (isRunning) return;
    if (!prompt.trim()) {
      setFormError("请输入提示词。");
      return;
    }
    if (referenceImages.length === 0) {
      setFormError("请至少上传一张参考图片。");
      return;
    }
    if (selectedProviders.length === 0) {
      setFormError("请至少选择一个模型。");
      return;
    }
    setActiveTool(null);
    setFormError(null);
    const size = RATIO_SIZE_MAP[ratio] ?? RATIO_SIZE_MAP[DEFAULT_RATIO];
    run({
      prompt,
      reference_images: referenceImages,
      providers: selectedProviders,
      size,
      params: {
        num_variations: numVariations,
        image_size: size,
        group_mode: groupMode,
      },
    });
  };

  const handleRegenerate = () => {
    reset();
    handleGenerate();
  };

  const handleReferenceUpload = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      const inputEl = event.target;
      const files = Array.from(inputEl.files ?? []);
      if (files.length === 0) {
        return;
      }
      const MAX_SINGLE_SIZE = 10 * 1024 * 1024;
      const MAX_TOTAL_SIZE = 64 * 1024 * 1024;

      const oversize = files.find((file) => file.size > MAX_SINGLE_SIZE);
      if (oversize) {
        setFormError(`图片 ${oversize.name} 超过 10MB 限制，请压缩后重新上传。`);
        inputEl.value = "";
        return;
      }

      const totalSize = referenceImageSizes.reduce((acc, cur) => acc + cur, 0) + files.reduce((acc, file) => acc + file.size, 0);
      if (totalSize > MAX_TOTAL_SIZE) {
        setFormError("所有参考图总大小不可超过 64MB，请删除部分图片后重试。");
        inputEl.value = "";
        return;
      }

      const readers = files.map(
        (file) =>
          new Promise<string>((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
              if (typeof reader.result === "string") {
                resolve(reader.result);
              } else {
                reject(new Error("读取图片失败"));
              }
            };
            reader.onerror = () => reject(new Error("读取图片失败"));
            reader.readAsDataURL(file);
          }),
      );

      Promise.all(readers)
        .then((results) => {
          setReferenceImages((prev) => [...prev, ...results]);
          setReferenceImageSizes((prev) => [...prev, ...files.map((file) => file.size)]);
          setFormError(null);
        })
        .catch((err) => {
          console.warn("读取参考图片失败", err);
          setFormError("读取参考图片失败，请重试。");
        })
        .finally(() => {
          inputEl.value = "";
        });
    },
    [referenceImageSizes],
  );

  const handleReferenceRemove = useCallback((index: number) => {
    setReferenceImages((prev) => prev.filter((_, idx) => idx !== index));
    setReferenceImageSizes((prev) => prev.filter((_, idx) => idx !== index));
  }, []);

  const toggleTool = useCallback((tool: ToolKey) => {
    setActiveTool((current) => (current === tool ? null : tool));
  }, []);

  const handleToggleSelect = (url: string) => {
    if (!url) {
      return;
    }
    setSelectedUrls((prev) =>
      prev.includes(url) ? prev.filter((item) => item !== url) : [...prev, url],
    );
  };

  const handleDownloadSelection = () => {
    selectedUrls.forEach((url, index) => {
      const link = document.createElement("a");
      link.href = url;
      link.download = `image-compose-${index + 1}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    });
  };

  useEffect(() => {
    setSelectedUrls([]);
  }, [result]);

  const stageLabel = useMemo(() => {
    switch (stage) {
      case ComposeStage.Uploading:
        return "上传图片";
      case ComposeStage.Generating:
        return "生成宣传图";
      case ComposeStage.Verifying:
        return "验证一致性";
      case ComposeStage.Completed:
        return "完成";
      default:
        return "准备就绪";
    }
  }, [stage]);

  const primaryProvider = selectedProviders[0] ?? "";

  return (
    <div className="flex flex-col gap-6 px-4 pb-12 pt-6 md:px-8 lg:px-12">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="rounded-3xl border border-white/10 bg-white/5 p-8 text-sm text-slate-200 backdrop-blur-xl"
      >
        <div className="space-y-3">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1 text-xs uppercase tracking-[0.3em] text-slate-400">
            Image Compose · Aesthetic Engine
          </span>
          <h1 className="text-4xl font-semibold tracking-tight text-white md:text-5xl">
            一拍即合 · 图生图营销助手
          </h1>
          <p className="max-w-3xl text-base leading-relaxed text-slate-300">
            上传参考图片，选择输出比例与模型，智能管线将生成多张电商宣传图并自动检查主体一致性。
          </p>
        </div>
      </motion.div>

      <div className="flex flex-col gap-8">
        <aside className="flex flex-col gap-6">
          <motion.div
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="flex flex-col gap-5 rounded-3xl border border-white/10 bg-white/5 p-6 text-sm text-slate-200 backdrop-blur-xl"
          >
          <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
            <div className="flex flex-col gap-4">
              <div className="relative">
                <textarea
                  value={prompt}
                  onChange={(event) => setPrompt(event.target.value)}
                  placeholder="描述场景、氛围、要突出的卖点..."
                  className="min-h-[220px] w-full rounded-2xl border border-white/10 bg-black/30 px-4 pb-4 pt-28 text-base text-white outline-none transition focus:border-emerald-400/60 focus:ring-2 focus:ring-emerald-400/30"
                />
                <div className="absolute left-4 right-4 top-4 flex flex-wrap items-center gap-3">
                  {referenceImages.map((image, index) => (
                    <div
                      key={`${image}-${index}`}
                      className="pointer-events-auto relative flex h-16 w-16 items-center justify-center overflow-hidden rounded-2xl border border-white/10 bg-black/40 shadow-lg shadow-black/30"
                    >
                      <img src={image} alt={`参考图片${index + 1}`} className="h-full w-full object-cover" />
                      <button
                        type="button"
                        onClick={(event) => {
                          event.preventDefault();
                          handleReferenceRemove(index);
                        }}
                        className="absolute -right-1 -top-1 inline-flex h-5 w-5 items-center justify-center rounded-full border border-white/20 bg-black/70 text-xs text-white transition hover:border-emerald-400/50 hover:bg-emerald-400/30"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                  <label className="pointer-events-auto flex h-16 w-16 cursor-pointer flex-col items-center justify-center gap-1 rounded-2xl border border-dashed border-white/15 bg-black/30 text-slate-400 transition hover:border-emerald-400/60 hover:text-emerald-200">
                    <input
                      type="file"
                      accept="image/*"
                      multiple
                      className="hidden"
                      onChange={handleReferenceUpload}
                      disabled={isRunning}
                    />
                    <PlusImageIcon />
                    <span className="text-[10px] text-slate-500">添加</span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <ToolButton
              icon="🎛️"
              label="比例与尺寸"
              active={activeTool === "ratio"}
              disabled={isRunning}
              onClick={() => toggleTool("ratio")}
            />
            <ToolButton
              icon="🧠"
              label={providerMap[primaryProvider]?.display_name ?? "选择模型"}
              active={activeTool === "model"}
              disabled={providersLoading}
              onClick={() => toggleTool("model")}
            />
            <ToolButton
              icon="🔁"
              label={
                groupMode ? `组图：${numVariations} 张` : `方案数：${numVariations}`
              }
              active={activeTool === "count"}
              disabled={isRunning}
              onClick={() => toggleTool("count")}
            />
          </div>

          {activeTool === "ratio" && (
            <div className="flex flex-wrap items-center gap-3 rounded-xl border border-white/10 bg-black/40 px-3 py-2">
              <label className="flex items-center gap-2 text-sm text-slate-200">
                <span className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
                  画面比例
                </span>
                <select
                  value={ratio}
                  onChange={(event) => handleRatioChange(event.target.value)}
                  disabled={isRunning}
                  className="h-10 rounded-lg border border-white/10 bg-black/30 px-3 text-sm text-white outline-none transition focus:border-emerald-400/60 focus:ring-2 focus:ring-emerald-400/30 disabled:cursor-not-allowed disabled:text-slate-500"
                >
                  {RATIO_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {`${option.label} (${option.size})`}
                    </option>
                  ))}
                </select>
              </label>
              <span className="text-xs text-slate-500">
                输出分辨率：{RATIO_SIZE_MAP[ratio] ?? RATIO_SIZE_MAP[DEFAULT_RATIO]}
              </span>
            </div>
          )}

          {activeTool === "model" && (
            <div className="flex flex-wrap items-center gap-3 rounded-xl border border-white/10 bg-black/40 px-3 py-2">
              <label className="flex items-center gap-2 text-sm text-slate-200">
                <span className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
                  生成模型
                </span>
                <select
                  value={primaryProvider}
                  onChange={(event) => handleModelChange(event.target.value)}
                  disabled={providersLoading}
                  className="h-10 min-w-[180px] rounded-lg border border-white/10 bg-black/30 px-3 text-sm text-white outline-none transition focus:border-emerald-400/60 focus:ring-2 focus:ring-emerald-400/30 disabled:cursor-not-allowed disabled:text-slate-500"
                >
                  {providerOptions.length === 0 && (
                    <option value="">
                      {providersLoading ? "正在加载..." : "暂无可用模型"}
                    </option>
                  )}
                  {providerOptions.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.display_name}
                    </option>
                  ))}
                </select>
              </label>
              {!!primaryProvider && (
                <span className="text-xs text-slate-500">
                  当前：{providerMap[primaryProvider]?.display_name ?? "未知模型"}
                </span>
              )}
            </div>
          )}

          {activeTool === "count" && (
            <div className="flex flex-col gap-3 rounded-xl border border-white/10 bg-black/40 px-3 py-2">
              <label className="flex items-center gap-2 text-sm text-slate-200">
                <input
                  type="checkbox"
                  checked={groupMode}
                  onChange={(event) => setGroupMode(event.target.checked)}
                  disabled={isRunning || primaryProvider !== "doubao_seedream"}
                  className="h-5 w-5 accent-emerald-400 disabled:cursor-not-allowed"
                />
                <span>生成组图（风格连续）</span>
                {primaryProvider !== "doubao_seedream" && (
                  <span className="text-xs text-slate-500">仅豆包 Seedream 支持组图</span>
                )}
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-200">
                <span className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
                  输出数量
                </span>
                <select
                  value={numVariations}
                  onChange={(event) => handleCountChange(Number(event.target.value))}
                  disabled={isRunning}
                  className="h-10 rounded-lg border border-white/10 bg-black/30 px-3 text-sm text-white outline-none transition focus:border-emerald-400/60 focus:ring-2 focus:ring-emerald-400/30 disabled:cursor-not-allowed disabled:text-slate-500"
                >
                  {Array.from(
                    { length: (groupMode ? 15 : 3) - (groupMode ? 2 : 1) + 1 },
                    (_, idx) => (groupMode ? 2 : 1) + idx,
                  ).map((item) => (
                    <option key={item} value={item}>
                      {groupMode ? `${item} 张` : `${item} 组`}
                    </option>
                  ))}
                </select>
              </label>
              <span className="text-xs text-slate-500">
                {groupMode
                  ? "豆包 Seedream 顺序生成，可一次输出最多 15 张风格连续的图片。"
                  : "生成多组候选方案，便于快速挑选喜欢的构图。"}
              </span>
            </div>
          )}

          <motion.button
            type="button"
            onClick={handleGenerate}
            disabled={isRunning || referenceImages.length === 0 || selectedProviders.length === 0}
            whileTap={{ scale: isRunning ? 1 : 0.98 }}
            className="inline-flex items-center justify-center self-center rounded-full bg-gradient-to-r from-emerald-500 via-teal-500 to-sky-500 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/25 transition hover:from-emerald-400 hover:via-teal-400 hover:to-sky-400 disabled:cursor-not-allowed disabled:bg-slate-600 disabled:shadow-none"
          >
            {isRunning ? "正在生成..." : "一键生成营销图"}
          </motion.button>
          </motion.div>

          {(error || formError) && (
            <div className="rounded-3xl border border-rose-400/40 bg-rose-500/10 p-4 text-sm text-rose-200">
              {formError ?? error}
            </div>
          )}
        </aside>

        <section className="flex flex-col gap-6">
          <ImageComposeResult
            result={result}
            stage={stage}
            stageLabel={stageLabel}
            onRegenerate={handleRegenerate}
            loading={isRunning}
            providers={providerMap}
            selectedUrls={selectedUrls}
            onToggleSelect={handleToggleSelect}
            onPreview={(url) => setPreviewImage(url)}
            onDownloadSelection={handleDownloadSelection}
          />
        </section>
      </div>

      <ImagePreviewModal src={previewImage} onClose={() => setPreviewImage(null)} />
    </div>
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

function ImageComposeResult({
  result,
  stage,
  stageLabel,
  onRegenerate,
  loading,
  providers,
  selectedUrls,
  onToggleSelect,
  onPreview,
  onDownloadSelection,
}: {
  result: ImageComposeResponse | null;
  stage: ComposeStageValue;
  stageLabel: string;
  onRegenerate: () => void;
  loading: boolean;
  providers: Record<string, ProviderInfo>;
  selectedUrls: string[];
  onToggleSelect: (url: string) => void;
  onPreview: (url: string) => void;
  onDownloadSelection: () => void;
}) {
  if (!result) {
    return (
      <div className="flex flex-col gap-4 rounded-3xl border border-dashed border-white/10 bg-white/5 p-6 text-sm text-slate-400">
        <div className="text-xs text-slate-500">当前进度：{stageLabel}</div>
        <div className="flex flex-1 flex-col items-center justify-center gap-3 text-center">
          <span className="text-lg text-white">上传参考图片即可开始生成</span>
          <p className="max-w-sm text-xs text-slate-500">
            系统将根据所选比例与模型生成多张候选图，并自动给出一致性建议，帮助你快速挑选适合的营销素材。
          </p>
        </div>
      </div>
    );
  }

  const bestLabel = providers[result.best_provider ?? ""]?.display_name ?? result.best_provider ?? "--";
  const outputResolution = result.image_size ?? "1024x1024";
  const bestIndex = result.results.findIndex((item) => item.image_url === result.best_image_url);
  const bestItem = bestIndex >= 0 ? result.results[bestIndex] : undefined;
  const groupMode = Boolean(result.group_mode);
  const bestSequential = groupMode && typeof bestItem?.sequence_index === "number";

  return (
    <motion.div
      initial={{ opacity: 0, x: 12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="flex min-h-[60vh] flex-col gap-5 rounded-3xl border border-white/10 bg-white/5 p-6 text-sm text-slate-200 backdrop-blur-xl"
    >
      <ComposeTimeline stage={stage} />
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>当前进度：{stageLabel}</span>
        <div className="flex items-center gap-3 text-slate-500">
          <span>输出分辨率：{outputResolution}</span>
          {result.best_image_url && <span>最佳模型：{bestLabel}</span>}
        </div>
      </div>

      {result.best_image_url ? (
        <div
          className={`relative overflow-hidden rounded-2xl border bg-black/30 transition ${
            selectedUrls.includes(result.best_image_url)
              ? "border-emerald-400/60"
              : "border-white/10"
          }`}
        >
          {bestSequential && (
            <span className="absolute left-4 bottom-4 z-10 rounded-full border border-emerald-400/50 bg-emerald-400/10 px-3 py-1 text-xs text-emerald-100">
              组图第 {(bestItem?.sequence_index ?? 0) + 1} 张
            </span>
          )}
          <button
            type="button"
            className={`absolute left-4 top-4 z-10 h-8 w-8 rounded-full border border-white/30 bg-black/50 text-white/80 transition ${
              selectedUrls.includes(result.best_image_url)
                ? "bg-emerald-500/50 text-white"
                : "hover:border-emerald-300/70"
            }`}
            onClick={() => onToggleSelect(result.best_image_url ?? "")}
            aria-label="选择图片"
          >
            {selectedUrls.includes(result.best_image_url) ? "✓" : "+"}
          </button>
          <button
            type="button"
            aria-label="放大查看"
            onClick={() => onPreview(result.best_image_url ?? "")}
            className="absolute right-4 top-4 inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/20 bg-black/50 text-white/80 transition hover:border-emerald-400/60 hover:text-white"
          >
            <MagnifierIcon />
          </button>
          <img
            src={result.best_image_url}
            alt="最佳结果"
            className="w-full object-contain"
            style={{ maxHeight: "70vh" }}
          />
        </div>
      ) : (
        <div className="flex h-64 items-center justify-center rounded-2xl border border-white/10 bg-black/30 text-slate-500">
          暂无最佳候选
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        {result.best_image_url && (
          <a
            href={result.best_image_url}
            download="compose-best.png"
            className="inline-flex items-center rounded-full border border-white/10 px-4 py-2 text-sm transition bg-white/10 text-slate-200 hover:border-emerald-400/60 hover:text-white"
          >
            下载最佳图片
          </a>
        )}
        <button
          type="button"
          onClick={onRegenerate}
          disabled={loading}
          className="inline-flex items-center rounded-full bg-emerald-500/80 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-emerald-500/40"
        >
          重新生成
        </button>
        <button
          type="button"
          onClick={onDownloadSelection}
          disabled={loading || selectedUrls.length === 0}
          className="inline-flex items-center rounded-full border border-white/10 px-4 py-2 text-sm text-slate-200 transition hover:border-emerald-400/60 hover:text-white disabled:cursor-not-allowed disabled:text-slate-600"
        >
          下载选中 ({selectedUrls.length})
        </button>
      </div>

      <div className="rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-400">
        <div className="text-sm text-white">候选结果</div>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          {result.results.map((item, index) => (
            <ComposeResultCard
              key={`${item.provider}-${item.image_url}`}
              data={item}
              provider={providers[item.provider]}
              selected={selectedUrls.includes(item.image_url ?? "")}
              onToggleSelect={(url) => url && onToggleSelect(url)}
              onPreview={(url) => onPreview(url)}
              imageSize={result.image_size}
              sequenceIndex={index}
              totalCount={result.results.length}
              groupMode={groupMode}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
}

function ComposeResultCard({
  data,
  provider,
  selected,
  onToggleSelect,
  onPreview,
  imageSize,
  sequenceIndex,
  totalCount,
  groupMode,
}: {
  data: ImageComposeResultItem;
  provider?: ProviderInfo;
  selected: boolean;
  onToggleSelect: (url: string) => void;
  onPreview: (url: string) => void;
  imageSize?: string;
  sequenceIndex: number;
  totalCount: number;
  groupMode: boolean;
}) {
  const verification = data.verification ?? {};
  const imageUrl = data.image_url ?? "";
  const providerLabel = provider?.display_name ?? data.provider;
  const resolution = imageSize ?? "1024x1024";
  const displayedSequence =
    typeof data.sequence_index === "number" ? data.sequence_index : sequenceIndex;
  const groupSize =
    typeof data.group_size === "number" ? data.group_size : totalCount;
  const isSequentialGroup =
    groupMode && groupSize > 1 && typeof displayedSequence === "number";

  return (
    <div
      className={`rounded-xl border bg-white/5 p-3 text-xs text-slate-300 transition ${
        selected ? "border-emerald-400/60" : "border-white/10"
      }`}
    >
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>
          {providerLabel}
          {isSequentialGroup ? (
            <span className="ml-2 rounded-full border border-emerald-400/50 bg-emerald-400/10 px-2 py-0.5 text-[10px] text-emerald-200">
              组图第 {(displayedSequence ?? 0) + 1} 张
            </span>
          ) : null}
        </span>
        <span>分辨率 · {resolution}</span>
      </div>
      <div className="relative mt-2 overflow-hidden rounded-lg border border-white/10">
        <button
          type="button"
          className={`absolute left-2 top-2 z-10 h-6 w-6 rounded-full border border-white/30 bg-black/50 text-white/80 transition ${
            selected ? "bg-emerald-500/50 text-white" : "hover:border-emerald-300/70"
          }`}
          onClick={() => imageUrl && onToggleSelect(imageUrl)}
          aria-label="选择图片"
        >
          {selected ? "✓" : "+"}
        </button>
        {imageUrl ? (
          <img src={imageUrl} alt={providerLabel} className="aspect-square w-full object-cover" />
        ) : (
          <div className="flex aspect-square items-center justify-center text-slate-500">无图片</div>
        )}
        {imageUrl && (
          <button
            type="button"
            aria-label="预览图片"
            onClick={() => onPreview(imageUrl)}
            className="absolute right-2 top-2 inline-flex h-7 w-7 items-center justify-center rounded-full border border-white/20 bg-black/50 text-white/80 transition hover:border-emerald-400/60 hover:text-white"
          >
            <MagnifierIcon size={14} />
          </button>
        )}
        {typeof data.composite_score === "number" && (
          <span className="absolute left-2 top-12 rounded-full bg-black/60 px-2 py-1 text-[11px] text-white/80">
            美感 {(data.composite_score * 10).toFixed(1)}
          </span>
        )}
      </div>
      <div className="mt-2 space-y-1 text-[11px] text-slate-500">
        <div>一致性状态：{verification.status ?? "待确认"}</div>
        {typeof verification.score === "number" && (
          <div>一致性分：{Math.round((verification.score ?? 0) * 100)} / 100</div>
        )}
        {verification.comment && <div className="text-slate-400">{verification.comment}</div>}
      </div>
    </div>
  );
}

function MagnifierIcon({ size = 18 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="11" cy="11" r="7" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
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
