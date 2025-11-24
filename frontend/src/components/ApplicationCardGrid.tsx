import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import type { ApplicationMeta } from "../types";

type ApplicationCardGridProps = {
  applications: ApplicationMeta[];
  categoryFilter?: string;
  onCategoryChange?: (category: string) => void;
};

const CATEGORY_OPTIONS = [
  { label: "全部", value: "all" },
  { label: "图像生成", value: "image" },
  { label: "视频生成", value: "video" },
  { label: "风格转换", value: "style" },
];

function resolveCategory(meta?: string) {
  if (!meta) return "all";
  if (meta === "image") return "图像生成";
  if (meta === "video") return "视频生成";
  if (meta === "style") return "风格转换";
  return meta;
}

export function ApplicationCardGrid({
  applications,
  categoryFilter = "all",
  onCategoryChange,
}: ApplicationCardGridProps) {
  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center gap-3 text-sm text-slate-300">
        {CATEGORY_OPTIONS.map((item) => {
          const active = categoryFilter === item.value;
          return (
            <button
              key={item.value}
              type="button"
              onClick={() => onCategoryChange?.(item.value)}
              className={`rounded-full border px-4 py-1.5 transition ${
                active
                  ? "border-emerald-400/70 bg-emerald-400/10 text-emerald-300"
                  : "border-white/10 bg-white/5 hover:border-emerald-400/40 hover:bg-emerald-400/5"
              }`}
            >
              {item.label}
            </button>
          );
        })}
      </div>

      <div className="grid gap-8 sm:grid-cols-2 xl:grid-cols-3">
        {applications.map((app) => {
          let targetHref = `/ai-detail/${app.id}`;
          if (app.id === "text2image") {
            targetHref = "/generate";
          } else if (app.id === "image-compose") {
            targetHref = "/image-compose";
          } else if (app.id === "aesthetic-workspace") {
            targetHref = "/workspace";
          }
          return (
          <motion.div
            key={app.id}
            whileHover={{ y: -4, scale: 1.01 }}
            transition={{ type: "spring", stiffness: 320, damping: 30 }}
            className="overflow-hidden rounded-3xl border border-white/10 bg-white/5 backdrop-blur-lg"
          >
            <Link to={targetHref} className="flex h-full flex-col">
              <div className="relative">
                <div className="aspect-[16/10] w-full overflow-hidden bg-gradient-to-br from-slate-800/80 to-slate-900">
                  <img
                    src={app.cover}
                    alt={app.title}
                    className="h-full w-full object-cover opacity-90"
                  />
                </div>
                <div className="absolute left-3 top-3 rounded-full border border-white/20 bg-black/50 px-3 py-1 text-xs font-medium uppercase tracking-widest text-white/70">
                  {resolveCategory(app.category)}
                </div>
              </div>
              <div className="flex flex-1 flex-col gap-4 px-5 py-6 text-slate-200">
                <div>
                  <h3 className="text-lg font-semibold text-white">
                    {app.title}
                  </h3>
                  <p className="mt-2 text-sm text-slate-400 line-clamp-2">
                    {app.desc}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {app.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full bg-white/5 px-3 py-1 text-xs text-slate-400"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
                <div className="mt-auto flex items-center justify-between text-xs text-slate-500">
                  <span>作者 · {app.author}</span>
                  <span>
                    ❤ {app.likes ?? "--"} · 👁 {app.views ?? "--"}
                  </span>
                </div>
              </div>
            </Link>
          </motion.div>
        )})}
      </div>
    </div>
  );
}
