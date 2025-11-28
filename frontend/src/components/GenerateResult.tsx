import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import type { PipelineStageValue } from "../hooks/usePipeline";
import type { PipelineResponse, ProviderInfo } from "../types";
import { ImagePreviewModal } from "./ImagePreviewModal";
import { PipelineTimeline } from "./PipelineTimeline";
import { AestheticAnalysisCard } from "./AestheticAnalysisCard";
import { METRIC_LABELS } from "../lib/constants";

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

        {result.best_composite_score !== undefined && (
          <AestheticAnalysisCard
            score={result.best_composite_score || 0}
            details={extractScoresFromCandidates(result)}
            review={
              result.review?.title && result.review?.analysis && result.review?.key_difference
                ? {
                    title: result.review.title,
                    analysis: result.review.analysis,
                    key_difference: result.review.key_difference,
                  }
                : undefined
            }
          />
        )}

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
                  {candidate.scores && Object.keys(candidate.scores).length > 0 && (
                    <div className="mt-3 space-y-1.5 text-[11px]">
                      {buildCandidateMetrics(candidate.scores).map((item) => (
                        <div key={item.key} className="flex items-center gap-2">
                          <span className="w-16 truncate text-slate-400">{item.label}</span>
                          <div className="relative h-2 flex-1 overflow-hidden rounded-full bg-slate-800/80">
                            <span
                              className="absolute left-0 top-0 h-full rounded-full bg-gradient-to-r from-emerald-400/80 via-emerald-300/70 to-cyan-300/70"
                              style={{ width: `${item.percent}%` }}
                            />
                          </div>
                          <span className="w-10 text-right text-slate-200">{item.display}</span>
                        </div>
                      ))}
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

function extractScoresFromCandidates(result: PipelineResponse): Record<string, number> {
  if (!result.candidates || result.candidates.length === 0) {
    return {};
  }
  const bestCandidate = result.candidates.find(
    (candidate) => candidate.image_url === result.best_image_url,
  );
  if (!bestCandidate?.scores) {
    return {};
  }
  const scores: Record<string, number> = {};
  for (const [key, value] of Object.entries(bestCandidate.scores)) {
    scores[key] = value;
  }
  if (result.best_composite_score !== undefined) {
    scores.holistic = result.best_composite_score;
  }
  return scores;
}

function buildCandidateMetrics(
  scores: Record<string, number | undefined | null>,
): Array<{ key: string; label: string; percent: number; display: string }> {
  const metricKeys = ["contrast_score", "color_score", "clarity_eval", "quality_score", "noise_eval"];
  return metricKeys
    .filter((key) => scores[key] !== undefined && scores[key] !== null)
    .map((key) => {
      const raw = Number(scores[key] ?? 0);
      const percent = Math.max(0, Math.min(100, Math.round(raw * 100)));
      const display = (raw * 10).toFixed(1);
      return {
        key,
        label: METRIC_LABELS[key] ?? key,
        percent,
        display,
      };
    });
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
