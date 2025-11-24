import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Button } from "../ui/Button";

const HERO_ITEMS = [
  {
    id: "hero-001",
    title: "咖啡店写真人像",
    subtitle: "柔焦光影 · 经典女仆装",
    image_url:
      "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=960&q=80",
    author: "RH Studio",
    likes: 5120,
    count: 2,
  },
  {
    id: "hero-002",
    title: "复古胶片调色",
    subtitle: "暖色调夜间街景",
    image_url:
      "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=960&q=80",
    author: "Nova",
    likes: 3862,
    count: 3,
  },
  {
    id: "hero-003",
    title: "银蓝色幻想剧照",
    subtitle: "电影感构图",
    image_url:
      "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=960&q=80",
    author: "Muse",
    likes: 2741,
    count: 4,
  },
];

const TABS = [
  { key: "works", label: "作品" },
  { key: "comments", label: "评论" },
];

export function AestheticHeroPreview() {
  const [activeIndex, setActiveIndex] = useState(0);
  const [activeTab, setActiveTab] = useState<string>(TABS[0].key);

  const current = useMemo(() => HERO_ITEMS[activeIndex % HERO_ITEMS.length], [activeIndex]);

  const handleNext = () => setActiveIndex((prev) => (prev + 1) % HERO_ITEMS.length);
  const handlePrev = () => setActiveIndex((prev) => (prev - 1 + HERO_ITEMS.length) % HERO_ITEMS.length);

  return (
    <div className="flex flex-1 flex-col gap-6 overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-6 text-slate-200 backdrop-blur-xl">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-white">实时生成预览</h2>
          <p className="mt-1 text-sm text-slate-400">
            运行后自动播放最新生成结果，可左右翻页查看不同批次。
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button type="button" variant="ghost" onClick={handlePrev}>
            ←
          </Button>
          <Button type="button" variant="ghost" onClick={handleNext}>
            →
          </Button>
        </div>
      </div>

      <motion.div
        key={current.id}
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="relative mx-auto w-full max-w-3xl overflow-hidden rounded-[32px] border border-white/10 bg-black/40"
      >
        <img
          src={current.image_url}
          alt={current.title}
          className="aspect-[3/4] w-full object-cover"
        />
        <div className="absolute left-5 top-5 rounded-full bg-black/60 px-4 py-1 text-xs text-white/80">
          {current.author}
        </div>
        <div className="absolute bottom-5 left-5 space-y-1 rounded-3xl bg-black/50 px-5 py-4 text-sm text-white">
          <div className="text-base font-semibold">{current.title}</div>
          <div className="text-xs text-white/70">{current.subtitle}</div>
          <div className="flex items-center gap-4 text-[11px] text-white/60">
            <span>❤ {current.likes}</span>
            <span>批次 {current.count}</span>
            <span>
              {activeIndex + 1}/{HERO_ITEMS.length}
            </span>
          </div>
        </div>
      </motion.div>

      <div className="border-t border-white/10 pt-4">
        <div className="flex gap-6 text-sm">
          {TABS.map((tab) => {
            const active = tab.key === activeTab;
            return (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key)}
                className={`relative pb-2 ${
                  active ? "text-emerald-300" : "text-slate-500 hover:text-emerald-200"
                }`}
              >
                {tab.label}
                {active && <span className="absolute inset-x-0 -bottom-1 h-0.5 rounded-full bg-emerald-300" />}
              </button>
            );
          })}
        </div>
        <div className="mt-4 rounded-2xl border border-white/10 bg-black/20 px-5 py-4 text-xs text-slate-400">
          {activeTab === "works" ? (
            <p>
              最新生成的作品将展示于此，支持导出至作品广场或继续调整提示词迭代。
            </p>
          ) : (
            <p>
              评论模块建设中，后续将支持模型建议、点赞排行榜等互动功能。
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
