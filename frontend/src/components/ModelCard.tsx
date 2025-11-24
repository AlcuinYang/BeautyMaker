import { motion } from "framer-motion";
import { Badge } from "./ui/Badge";

interface ModelCardProps {
  id: string;
  name: string;
  description: string;
  icon?: string | null;
  isFree: boolean;
  isActive: boolean;
  onSelect: (id: string) => void;
  isSelected: boolean;
}

export function ModelCard({
  id,
  name,
  description,
  icon,
  isFree,
  isActive,
  onSelect,
  isSelected,
}: ModelCardProps) {
  return (
    <motion.button
      type="button"
      onClick={() => onSelect(id)}
      whileHover={{ y: -4, scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      className={`flex h-full flex-col gap-4 rounded-2xl border bg-white/5 p-5 text-left shadow-lg transition ${
        isSelected
          ? "border-teal-400/80 shadow-emerald-500/40"
          : "border-white/10 hover:border-emerald-300/60 hover:shadow-emerald-500/20"
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className={`text-lg ${isActive ? "text-emerald-300" : "text-rose-400"}`}>
            {isActive ? "🟢" : "🔴"}
          </span>
          <div className="flex flex-col">
            <span className="text-sm text-slate-400">模型 ID</span>
            <span className="text-xs text-slate-500">{id}</span>
          </div>
        </div>
        {icon ? (
          <img src={icon} alt={name} className="h-14 w-14 object-contain" />
        ) : (
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-white/10 text-lg text-slate-300">
            ⚙️
          </div>
        )}
      </div>

      <div className="space-y-2">
        <h3 className="text-lg font-semibold text-white">{name}</h3>
        <p className="text-sm leading-relaxed text-slate-400 line-clamp-3">{description}</p>
      </div>

      <div className="mt-auto flex items-center gap-2">
        <Badge variant={isFree ? "free" : "paid"}>{isFree ? "免费" : "付费"}</Badge>
        {isSelected && (
          <Badge variant="active">已选择</Badge>
        )}
      </div>
    </motion.button>
  );
}
