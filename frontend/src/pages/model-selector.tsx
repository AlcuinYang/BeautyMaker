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
    <div className="min-h-screen bg-[#07070a] text-white">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 pb-20 pt-16 md:px-10">
        <motion.header
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="space-y-5"
        >
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1 text-xs uppercase tracking-[0.3em] text-slate-400">
            Model Selector · Aesthetic Engine
          </span>
          <div className="space-y-4">
            <h1 className="text-4xl font-semibold tracking-tight text-white md:text-5xl">
              选择你想使用的模型
            </h1>
            <p className="max-w-2xl text-base leading-relaxed text-slate-400">
              从免费模型到实验室模块，挑选最适合当前任务的 AI 能力。我们会自动统一输入输出格式，让你专注于创造灵感。
            </p>
          </div>
        </motion.header>

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
