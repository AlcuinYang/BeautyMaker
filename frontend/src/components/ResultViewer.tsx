import { motion } from "framer-motion";
import { useMemo, useState } from "react";
import type { AestheticResponse } from "../types";
import { ImagePreviewModal } from "./ImagePreviewModal";
import { ScoreRadarChart } from "./ScoreRadarChart";

type ResultViewerProps = {
  result: AestheticResponse | null;
  isLoading: boolean;
  moduleNameMap?: Record<string, string>;
};

const DEFAULT_MODULE_LABELS: Record<string, string> = {
  holistic: "综合美感",
  color_score: "光色表现",
  contrast_score: "构图表达",
  clarity_eval: "清晰完整度",
  noise_eval: "风格协调性",
  quality_score: "情绪感染力",
};

export function ResultViewer({
  result,
  isLoading,
  moduleNameMap = {},
}: ResultViewerProps) {
  const mergedModuleNameMap = useMemo(
    () => ({ ...DEFAULT_MODULE_LABELS, ...moduleNameMap }),
    [moduleNameMap],
  );
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const gallery = useMemo(() => {
    if (!result) return [];
    const images = result.images && result.images.length > 0
      ? result.images
      : result.image_url
        ? [result.image_url]
        : [];
    return images;
  }, [result]);

  const radarData = useMemo(() => {
    if (!result?.scores) return [];
    return Object.entries(result.scores)
      .filter(([key]) => key !== "composite_score")
      .map(([key, value]) => ({
        metric: mergedModuleNameMap[key] ?? key,
        score: Number(((value ?? 0) * 10).toFixed(1)),
      }));
  }, [result, mergedModuleNameMap]);

  const primaryImage =
    result?.best_candidate ??
    (gallery.length > 0 ? gallery[0] : result?.image_url ?? "");

  return (
    <div className="flex h-full flex-col gap-6 rounded-3xl border border-white/10 bg-white/5 p-6 text-slate-200 backdrop-blur-xl">
      <header className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">生成结果</h2>
          <p className="text-xs text-slate-400">
            从模糊到清晰，记录美学引擎评分。
          </p>
        </div>
        {typeof result?.composite_score === "number" && (
          <span className="rounded-full border border-emerald-400/50 bg-emerald-400/10 px-4 py-1 text-xs font-semibold text-emerald-200">
            美感评分 {((result.composite_score ?? 0) * 10).toFixed(1)}
          </span>
        )}
      </header>

      <div className="relative flex-1 overflow-hidden rounded-2xl border border-white/10 bg-black/30">
        {primaryImage ? (
          <motion.img
            key={primaryImage}
            src={primaryImage}
            alt="生成结果"
            initial={{ filter: "blur(24px)", scale: 1.04, opacity: 0.4 }}
            animate={{ filter: "blur(0px)", scale: 1, opacity: 1 }}
            transition={{ duration: 0.9, ease: "easeOut" }}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-slate-400">
            <span className="text-lg font-semibold">等待运行结果</span>
            <span className="text-xs">
              点击左侧“运行生成任务”后，这里会展示输出画面。
            </span>
          </div>
        )}

        {result?.best_candidate && (
          <span className="absolute left-4 top-4 rounded-full border border-emerald-400/60 bg-emerald-400/10 px-3 py-1 text-xs font-semibold text-emerald-200 backdrop-blur-sm">
            最美图片
          </span>
        )}

        {primaryImage && (
          <button
            type="button"
            aria-label="放大查看"
            onClick={() => setPreviewImage(primaryImage)}
            className="absolute right-4 top-4 inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/20 bg-black/50 text-white/80 transition hover:border-emerald-400/60 hover:text-white"
          >
            <MagnifierIcon />
          </button>
        )}

        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-md">
            <div className="flex flex-col items-center gap-2">
              <div className="h-12 w-12 animate-spin rounded-full border-4 border-emerald-400 border-t-transparent" />
              <span className="text-xs text-emerald-200">正在生成中...</span>
            </div>
          </div>
        )}
      </div>

      {gallery.length > 1 && (
        <div className="flex gap-3 overflow-x-auto pb-2">
          {gallery.map((url) => (
            <div key={url} className="group relative">
              <motion.img
                src={url}
                whileHover={{ scale: 1.02 }}
                onClick={() => setPreviewImage(url)}
                className={`h-16 w-16 cursor-pointer rounded-xl border border-white/10 object-cover ${
                  url === primaryImage ? "ring-2 ring-emerald-400/70" : ""
                }`}
              />
              <span className="absolute inset-0 hidden items-center justify-center rounded-xl bg-black/50 text-[10px] text-white/80 backdrop-blur-sm group-hover:flex">
                点击放大
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="flex h-56 flex-col gap-3 rounded-2xl border border-white/10 bg-black/30 p-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold text-white">评分雷达图</span>
          <span className="text-xs text-slate-500">
            美感维度（1-10 分） 越高越好
          </span>
        </div>
        <ScoreRadarChart data={radarData} />
      </div>

      {result?.message && (
        <div className="rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-xs text-slate-400">
          {result.message}
        </div>
      )}

      <ImagePreviewModal src={previewImage} onClose={() => setPreviewImage(null)} />
    </div>
  );
}

function MagnifierIcon() {
  return (
    <svg
      width="18"
      height="18"
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
