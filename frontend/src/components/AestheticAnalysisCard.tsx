import { motion } from "framer-motion";
import { METRIC_LABELS } from "../lib/constants";
import { ScoreRadarChart } from "./ScoreRadarChart";

interface AestheticAnalysisCardProps {
  score: number;
  details: Record<string, number>;
  review?: {
    title: string;
    analysis: string;
    key_difference: string;
  };
  isLoading?: boolean;
}

export function AestheticAnalysisCard({
  score,
  details,
  review,
  isLoading = false,
}: AestheticAnalysisCardProps) {
  const normalizedScore = score > 1 ? score : score * 10;

  const chartData = Object.entries(details)
    .filter(([key]) => key !== "holistic")
    .map(([key, value]) => ({
      key,
      label: METRIC_LABELS[key] || key,
      score: value * 10,
    }));

  if (isLoading) {
    return (
      <div className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
        <div className="flex animate-pulse items-center justify-center space-y-4">
          <div className="h-32 w-32 rounded-full bg-white/10" />
          <div className="ml-6 flex-1 space-y-3">
            <div className="h-6 w-3/4 rounded bg-white/10" />
            <div className="h-4 w-full rounded bg-white/10" />
            <div className="h-4 w-5/6 rounded bg-white/10" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.08] to-white/[0.03] p-6 backdrop-blur-xl"
    >
      <div className="mb-6 flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500/20 to-teal-500/20">
            <span className="text-xl">⚡</span>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">美学分析</h3>
            <p className="text-xs text-slate-400">AI 质检专家评估</p>
          </div>
        </div>
        <div className="ml-auto">
          <CircularProgress score={normalizedScore} />
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="flex items-center justify-center rounded-2xl border border-white/10 bg-black/30 p-4">
          <div className="h-[260px] w-full">
            <ScoreRadarChart data={chartData} compositeScore={details.holistic} />
          </div>
        </div>

        <div className="flex flex-col justify-center space-y-4">
          {review ? (
            <>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">🏆</span>
                  <h4 className="text-lg font-semibold text-emerald-200">{review.title}</h4>
                </div>
                <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1">
                  <span className="text-xs font-medium text-emerald-300">核心差异</span>
                  <span className="text-xs text-emerald-100">{review.key_difference}</span>
                </div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="text-sm leading-relaxed text-slate-200">{review.analysis}</p>
              </div>
            </>
          ) : (
            <div className="flex h-full flex-col items-center justify-center space-y-3 rounded-xl border border-dashed border-white/10 bg-white/5 p-6 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-700/50">
                <span className="text-xl">📊</span>
              </div>
              <div>
                <p className="text-sm font-medium text-white">评分分析</p>
                <p className="mt-1 text-xs text-slate-400">
                  根据多维度指标综合评估
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(details).map(([key, value]) => (
                  <div
                    key={key}
                    className="rounded-full border border-white/10 bg-white/5 px-3 py-1"
                  >
                    <span className="text-xs text-slate-300">
                      {(METRIC_LABELS[key] || key)}: {(value * 10).toFixed(1)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

function CircularProgress({ score }: { score: number }) {
  const percentage = (score / 10) * 100;
  const circumference = 2 * Math.PI * 40;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const getScoreColor = (s: number) => {
    if (s >= 8) return "from-emerald-400 to-teal-400";
    if (s >= 6) return "from-blue-400 to-cyan-400";
    if (s >= 4) return "from-amber-400 to-orange-400";
    return "from-rose-400 to-pink-400";
  };

  return (
    <div className="relative h-24 w-24">
      <svg className="h-full w-full -rotate-90 transform">
        <circle
          cx="48"
          cy="48"
          r="40"
          stroke="currentColor"
          strokeWidth="6"
          fill="none"
          className="text-white/10"
        />
        <circle
          cx="48"
          cy="48"
          r="40"
          stroke="url(#gradient)"
          strokeWidth="6"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
        <defs>
          <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop
              offset="0%"
              className={`${getScoreColor(score).split(" ")[0].replace("from-", "")}`}
              stopColor="currentColor"
            />
            <stop
              offset="100%"
              className={`${getScoreColor(score).split(" ")[1].replace("to-", "")}`}
              stopColor="currentColor"
            />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-white">{score.toFixed(1)}</span>
        <span className="text-[10px] text-slate-400">/ 10</span>
      </div>
    </div>
  );
}
