import { motion } from "framer-motion";

export function LoadingSpinner() {
  return (
    <div className="flex flex-col items-center gap-3 text-slate-400">
      <motion.div
        className="h-12 w-12 rounded-full border-2 border-transparent"
        style={{ borderTopColor: "#34d399", borderBottomColor: "#22d3ee" }}
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 1.2, ease: "easeInOut" }}
      />
      <span className="text-sm">正在加载模型...</span>
    </div>
  );
}
