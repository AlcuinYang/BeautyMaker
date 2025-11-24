import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api } from "../lib/api";
import type { ApplicationMeta } from "../types";
import { ApplicationCardGrid } from "../components/ApplicationCardGrid";

export default function AiApplicationPage() {
  const [apps, setApps] = useState<ApplicationMeta[]>([]);
  const [filtered, setFiltered] = useState<ApplicationMeta[]>([]);
  const [category, setCategory] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    api
      .listApps()
      .then((data) => {
        if (!mounted) return;
        setApps(data);
        setFiltered(data);
      })
      .catch((err) => {
        console.error(err);
        if (mounted) setError(err instanceof Error ? err.message : "加载失败");
      })
      .finally(() => mounted && setLoading(false));

    return () => {
      mounted = false;
    };
  }, []);

  const handleCategoryChange = (value: string) => {
    setCategory(value);
    if (value === "all") {
      setFiltered(apps);
    } else {
      setFiltered(
        apps.filter((app) => (app.category ?? "all") === value),
      );
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0b0f] text-white">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 pb-20 pt-16 md:px-10">
        <motion.header
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="space-y-4"
        >
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1 text-xs uppercase tracking-[0.3em] text-slate-400">
            Aesthetic Engine Playground
          </span>
          <h1 className="text-4xl font-semibold tracking-tight text-white md:text-5xl">
            多模型一站式
            <span className="block bg-gradient-to-r from-emerald-400 via-teal-300 to-sky-400 bg-clip-text text-transparent">
              AI 创作与工作流中心
            </span>
          </h1>
          <p className="max-w-2xl text-base leading-relaxed text-slate-400">
            最美丽的图片生成工具。
          </p>
        </motion.header>

        {loading ? (
          <div className="flex h-64 items-center justify-center rounded-3xl border border-white/10 bg-white/5 text-slate-400">
            正在加载应用列表...
          </div>
        ) : error ? (
          <div className="rounded-3xl border border-rose-400/50 bg-rose-500/10 p-6 text-sm text-rose-200">
            {error}
          </div>
        ) : (
          <ApplicationCardGrid
            applications={filtered}
            categoryFilter={category}
            onCategoryChange={handleCategoryChange}
          />
        )}
      </div>
    </div>
  );
}
