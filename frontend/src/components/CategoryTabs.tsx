import { motion } from "framer-motion";

interface CategoryTabsProps {
  categories: string[];
  active: string;
  onChange: (category: string) => void;
}

const CATEGORY_LABELS: Record<string, string> = {
  all: "全部模型",
  image_generation: "图像生成",
  aesthetic_analysis: "美学分析",
  enhancement: "增强模块",
};

export function CategoryTabs({ categories, active, onChange }: CategoryTabsProps) {
  const items = ["all", ...categories];

  return (
    <div className="relative flex flex-wrap gap-3 text-sm text-slate-400">
      {items.map((category) => {
        const label = CATEGORY_LABELS[category] ?? category;
        const isActive = active === category;
        return (
          <button
            key={category}
            type="button"
            onClick={() => onChange(category)}
            className={`relative rounded-full px-5 py-2 transition ${
              isActive
                ? "text-white"
                : "hover:text-emerald-200"
            }`}
          >
            {isActive && (
              <motion.span
                layoutId="category-pill"
                className="absolute inset-0 rounded-full bg-emerald-500/20"
                transition={{ type: "spring", stiffness: 260, damping: 30 }}
              />
            )}
            <span className="relative z-10">{label}</span>
          </button>
        );
      })}
    </div>
  );
}
