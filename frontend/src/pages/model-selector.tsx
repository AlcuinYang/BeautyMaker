import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { CategoryTabs } from "../components/CategoryTabs";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ModelCard } from "../components/ModelCard";
import { api } from "../lib/api";
import type { ProviderInfo } from "../types";

export default function ModelSelectorPage() {
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [activeCategory, setActiveCategory] = useState("all");
  const [selectedProvider, setSelectedProvider] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("selectedProvider");
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    let mounted = true;
    api
      .listProviders()
      .then((data) => {
        if (!mounted) return;
        setProviders(data);
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

  const categories = useMemo(() => {
    const result = new Set<string>();
    providers.forEach((item) => result.add(item.category));
    return Array.from(result);
  }, [providers]);

  const filteredProviders = useMemo(() => {
    if (activeCategory === "all") return providers;
    return providers.filter((item) => item.category === activeCategory);
  }, [providers, activeCategory]);

  const handleSelect = (id: string) => {
    setSelectedProvider(id);
    localStorage.setItem("selectedProvider", id);
    navigate(`/ai-detail/${id}`);
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      <div className="relative w-full overflow-hidden bg-slate-950">
        <div className="absolute -left-20 -top-24 h-[500px] w-[500px] rounded-full bg-[#7B61FF]/20 blur-[120px] z-0" />
        <div className="absolute bottom-[-80px] right-[-30px] h-[400px] w-[400px] rounded-full bg-[#00E5FF]/15 blur-[100px] z-0" />
        <div className="relative z-10 mx-auto flex min-h-[70vh] w-full max-w-6xl flex-col items-center justify-center px-6 py-20 text-center md:px-10">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="flex flex-col items-center"
          >
            <span className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-medium tracking-[0.3em] text-white/70 backdrop-blur-md">
              MODEL SELECTOR · AESTHETIC ENGINE
            </span>
            <h1 className="mb-6 text-5xl font-bold tracking-tight text-white drop-shadow md:text-7xl">
              多模型一站式 AI 创作与工作流中心
            </h1>
            <p className="mb-10 max-w-2xl text-xl leading-relaxed text-slate-400">
              重构电商美学，让 AI 更懂商业摄影。
            </p>
            <button
              type="button"
              className="rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 px-8 py-4 text-lg font-semibold text-white shadow-lg shadow-cyan-500/25 transition-transform hover:scale-105"
              onClick={() => navigate("/ai-application")}
            >
              立即开始创作
            </button>
          </motion.div>
        </div>
      </div>
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 pb-20 pt-16 md:px-10">

        {loading ? (
          <div className="flex h-72 items-center justify-center rounded-3xl border border-white/10 bg-white/5">
            <LoadingSpinner />
          </div>
        ) : error ? (
          <div className="rounded-3xl border border-rose-400/50 bg-rose-500/10 p-6 text-sm text-rose-200">
            {error}
          </div>
        ) : (
          <>
            <CategoryTabs
              categories={categories}
              active={activeCategory}
              onChange={setActiveCategory}
            />

            <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
              {filteredProviders.map((provider) => (
                <ModelCard
                  key={provider.id}
                  id={provider.id}
                  name={provider.display_name}
                  description={provider.description}
                  icon={provider.icon}
                  isFree={provider.is_free}
                  isActive={provider.is_active}
                  onSelect={handleSelect}
                  isSelected={selectedProvider === provider.id}
                />
              ))}
            </div>
          </>
        )}

        <footer className="mt-16 flex flex-col gap-2 text-sm text-slate-500">
          <span>Powered by Aesthetic Engine · 多模型适配层</span>
          <span>支持 Pollinations / HuggingFace / Stability / Gemini / Fal.ai 等来源。</span>
        </footer>
      </div>
    </div>
  );
}
