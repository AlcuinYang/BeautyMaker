import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import type { PipelineStageValue } from "../hooks/usePipeline";
import type { PipelineResponse, ProviderInfo } from "../types";
import { ImagePreviewModal } from "./ImagePreviewModal";
import { PipelineTimeline } from "./PipelineTimeline";
import { ScoreRadarChart } from "./ScoreRadarChart";

interface GenerateResultProps {
  result: PipelineResponse | null;
  onRegenerate: () => void;
  stage: PipelineStageValue;
  disabled?: boolean;
  providerMap?: Record<string, ProviderInfo>;
}

export function GenerateResult({
  result,
  onRegenerate,
  stage,
  disabled = false,
  providerMap = {},
}: GenerateResultProps) {
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [selectedUrls, setSelectedUrls] = useState<string[]>([]);
  const radarData = useMemo(() => buildRadarData(result), [result]);
  const bestProviderName = useMemo(() => {
    if (!result?.best_image_url || !result.candidates) return null;
    const bestCandidate = result.candidates.find(
      (candidate) => candidate.image_url === result.best_image_url,
    );
    if (!bestCandidate?.provider) return null;
    const provider = providerMap[bestCandidate.provider];
    return provider?.display_name ?? bestCandidate.provider;
  }, [result, providerMap]);

  useEffect(() => {
    setSelectedUrls([]);
  }, [result]);

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
      link.download = `text2image-${index + 1}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    });
  };

  if (!result) {
    return (
      <div className="flex h-full flex-col gap-4">
        <PipelineTimeline stage={stage} />
        <div className="flex flex-1 flex-col items-center justify-center gap-3 rounded-3xl border border-dashed border-white/10 bg-white/5 p-6 text-sm text-slate-400">
          <span className="text-lg text-white">欢迎体验智能生成</span>
          <p className="max-w-sm text-center text-xs text-slate-500">
            选择模型并输入提示词，系统会自动完成多模型生成、美学评分，为你选出最具美感的最终图片。
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col gap-4">
      <PipelineTimeline stage={stage} />
      <motion.div
        initial={{ opacity: 0, x: 12 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="flex min-h-[60vh] flex-col gap-6 rounded-3xl border border-white/10 bg-white/5 p-6 text-slate-200 backdrop-blur-xl"
      >
        <div className="flex flex-col gap-4 md:flex-row">
          <div className="flex-1">
            <div
              className={`relative overflow-hidden rounded-2xl border bg-black/30 transition ${
                result.best_image_url && selectedUrls.includes(result.best_image_url)
                  ? "border-emerald-400/60"
                  : "border-white/10"
              }`}
            >
              {result.best_image_url ? (
                <motion.img
                  key={result.best_image_url}
                  src={result.best_image_url}
                  alt="最优结果"
                  initial={{ filter: "blur(24px)", scale: 1.05, opacity: 0.4 }}
                  animate={{ filter: "blur(0px)", scale: 1, opacity: 1 }}
                  transition={{ duration: 0.8, ease: "easeOut" }}
                  className="w-full object-contain"
                  style={{ maxHeight: "70vh" }}
                />
              ) : (
                <div className="flex h-80 items-center justify-center text-slate-400">
                  未返回图片
                </div>
              )}
              {result.best_image_url && (
                <button
                  type="button"
                  className={`absolute left-4 top-4 z-10 h-8 w-8 rounded-full border border-white/30 bg-black/50 text-white/80 transition ${
                    selectedUrls.includes(result.best_image_url)
                      ? "bg-emerald-500/50 text-white"
                      : "hover:border-emerald-300/70"
                  }`}
                  onClick={() => handleToggleSelect(result.best_image_url ?? "")}
                  aria-label="选择图片"
                >
                  {selectedUrls.includes(result.best_image_url) ? "✓" : "+"}
                </button>
              )}
              <span className="absolute left-4 top-12 rounded-full bg-emerald-500/20 px-3 py-1 text-xs font-semibold text-emerald-100">
                美感评分{" "}
                {result.best_composite_score !== undefined && result.best_composite_score !== null
                  ? (result.best_composite_score * 10).toFixed(1)
                  : "--"}
              </span>
              {bestProviderName && (
                <span className="absolute left-4 bottom-4 rounded-full bg-black/60 px-3 py-1 text-xs text-slate-200">
                  {bestProviderName}
                </span>
              )}
              {result.best_image_url && (
                <button
                  type="button"
                  aria-label="放大查看"
                  onClick={() => setPreviewImage(result.best_image_url ?? "")}
                  className="absolute right-4 top-4 inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/20 bg-black/50 text-white/80 transition hover:border-emerald-400/60 hover:text-white"
                >
                  <MagnifierIcon />
                </button>
              )}
            </div>
          </div>

          <div className="flex-1 space-y-4">
            <div className="h-56 rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-400">
              <div className="mb-2 flex items-center justify-between text-sm text-white">
                <span>美学维度评分</span>
                <span>1 - 10</span>
              </div>
              <ScoreRadarChart data={radarData} />
            </div>

            <div className="rounded-2xl border border-white/10 bg-black/30 p-4 text-sm text-slate-300">
              <h3 className="text-base font-semibold text-white">系统点评</h3>
              <p className="mt-2 text-sm text-slate-400">
                {result.summary ?? "该图片在多项指标表现均衡。"}
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <a
                href={result.best_image_url ?? "#"}
                download={result.best_image_url ? "best-image.png" : undefined}
                className={`inline-flex items-center rounded-full border border-white/10 px-4 py-2 text-sm transition ${
                  result.best_image_url && !disabled
                    ? "bg-white/10 text-slate-200 hover:border-emerald-400/60 hover:text-white"
                    : "cursor-not-allowed bg-white/5 text-slate-600"
                }`}
                aria-disabled={disabled || !result.best_image_url}
                onClick={(event) => {
                  if (disabled || !result.best_image_url) {
                    event.preventDefault();
                  }
                }}
              >
                下载图片
              </a>
              <button
                type="button"
                onClick={onRegenerate}
                disabled={disabled}
                className="inline-flex items-center rounded-full bg-emerald-500/80 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-emerald-500/40"
              >
                重新生成
              </button>
              <button
                type="button"
                onClick={handleDownloadSelection}
                disabled={disabled || selectedUrls.length === 0}
                className="inline-flex items-center rounded-full border border-white/10 px-4 py-2 text-sm text-slate-200 transition hover:border-emerald-400/60 hover:text-white disabled:cursor-not-allowed disabled:text-slate-600"
              >
                下载选中 ({selectedUrls.length})
              </button>
            </div>
          </div>
        </div>

        {result.candidates && result.candidates.length > 1 && (
          <div className="rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-xs text-slate-400">
            <span className="text-sm text-white">候选对比</span>
            <div className="mt-3 grid gap-3 md:grid-cols-3">
              {result.candidates.map((candidate, index) => (
                <div
                  key={`${candidate.image_url ?? "candidate"}-${index}`}
                  className={`group relative rounded-xl border bg-white/5 p-3 transition ${
                    selectedUrls.includes(candidate.image_url ?? "")
                      ? "border-emerald-400/60"
                      : "border-white/10"
                  }`}
                >
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>
                      候选 {index + 1}
                      {candidate.provider ? ` · ${(providerMap[candidate.provider]?.display_name) ?? candidate.provider}` : ""}
                    </span>
                    <span>
                      美感评分{" "}
                      {candidate.composite_score !== undefined && candidate.composite_score !== null
                        ? (candidate.composite_score * 10).toFixed(1)
                        : "--"}
                    </span>
                  </div>
                  {candidate.image_url ? (
                    <div className="relative mt-2">
                      <button
                        type="button"
                        className={`absolute left-3 top-3 z-10 h-7 w-7 rounded-full border border-white/30 bg-black/50 text-white/80 transition ${
                          selectedUrls.includes(candidate.image_url ?? "")
                            ? "bg-emerald-500/50 text-white"
                            : "hover:border-emerald-300/70"
                        }`}
                        onClick={() => handleToggleSelect(candidate.image_url ?? "")}
                        aria-label="选择候选图片"
                      >
                        {selectedUrls.includes(candidate.image_url ?? "") ? "✓" : "+"}
                      </button>
                      <img
                        src={candidate.image_url}
                        alt={`候选 ${index + 1}`}
                        className="aspect-square w-full rounded-lg object-cover"
                      />
                      <button
                        type="button"
                        aria-label="放大候选图"
                        onClick={() => setPreviewImage(candidate.image_url ?? "")}
                        className="absolute right-3 top-3 hidden h-7 w-7 items-center justify-center rounded-full border border-white/20 bg-black/50 text-white/80 transition group-hover:flex hover:border-emerald-400/60 hover:text-white"
                      >
                        <MagnifierIcon size={14} />
                      </button>
                    </div>
                  ) : (
                    <div className="mt-2 flex aspect-square items-center justify-center rounded-lg bg-black/30 text-slate-500">
                      无图片
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </motion.div>
      <ImagePreviewModal src={previewImage} onClose={() => setPreviewImage(null)} />
    </div>
  );
}

function buildRadarData(result: PipelineResponse | null) {
  if (!result?.candidates || result.candidates.length === 0) {
    return [];
  }
  const best =
    result.candidates.find((item) => item.image_url === result.best_image_url) ??
    result.candidates.reduce((acc, item) => {
      if (!acc) return item;
      return (item.composite_score ?? 0) > (acc.composite_score ?? 0) ? item : acc;
    });

  const scores = best?.scores ?? {};
  const LABEL_MAP: Record<string, string> = {
    holistic: "综合美感",
    color_score: "光色表现",
    contrast_score: "构图表达",
    clarity_eval: "清晰完整度",
    noise_eval: "风格协调性",
    quality_score: "情绪感染力",
  };
  return Object.entries(scores).map(([key, value]) => ({
    metric: LABEL_MAP[key] ?? key,
    score: Number(((value ?? 0) * 10).toFixed(1)),
  }));
}

function MagnifierIcon({ size = 18 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle cx="11" cy="11" r="6" stroke="currentColor" strokeWidth="2" />
      <line x1="15.5" y1="15.5" x2="21" y2="21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="11" y1="8" x2="11" y2="14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="8" y1="11" x2="14" y2="11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
