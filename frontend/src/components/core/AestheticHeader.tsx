import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

export function AestheticHeader() {
  const [query, setQuery] = useState("");

  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="sticky top-0 z-30 border-b border-white/10 bg-white/10 backdrop-blur-xl"
    >
      <div className="mx-auto flex w-full max-w-7xl items-center gap-6 px-6 py-4 md:px-10">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-emerald-400/60 to-sky-400/60" />
          <span className="text-lg font-semibold tracking-wide text-white">Aesthetic Engine</span>
        </div>

        <div className="relative hidden flex-1 items-center md:flex">
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search models or aesthetics…"
            className="h-11 bg-black/40 pl-11"
          />
          <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-sm text-slate-500">
            🔍
          </span>
        </div>

        <div className="ml-auto flex items-center gap-3">
          <Button variant="secondary" className="hidden md:inline-flex">
            上传
          </Button>
          <Button variant="ghost" className="border border-white/15 bg-white/5 px-5">
            登录
          </Button>
        </div>
      </div>
    </motion.header>
  );
}
