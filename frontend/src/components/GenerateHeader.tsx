import { motion } from "framer-motion";
 
export function GenerateHeader() {
  return (
    <div className="flex flex-col gap-6">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="rounded-3xl border border-white/10 bg-white/5 p-8 text-sm text-slate-200 backdrop-blur-xl"
      >
        <div className="space-y-3">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1 text-xs uppercase tracking-[0.3em] text-slate-400">
            Smart Pipeline · Aesthetic Engine
          </span>
          <h1 className="text-4xl font-semibold tracking-tight text-white md:text-5xl">
            文生图 · 智能管线
          </h1>
          <p className="max-w-3xl text-base leading-relaxed text-slate-300">
            输入灵感后选择一个或多个模型，系统会自动扩写提示词、并行出图并完成美学评分，帮助你挑选最具美感的结果。
          </p>
        </div>
      </motion.div>
    </div>
  );
}
