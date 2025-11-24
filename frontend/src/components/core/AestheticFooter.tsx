export function AestheticFooter() {
  return (
    <footer className="border-t border-white/10 bg-white/5">
      <div className="mx-auto flex w-full max-w-7xl flex-col items-center gap-2 px-6 py-4 text-xs text-slate-400 md:flex-row md:justify-between md:px-10">
        <div className="flex items-center gap-3">
          <span>Language</span>
          <select className="rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs text-slate-300 outline-none">
            <option value="zh">中文</option>
            <option value="en">English</option>
          </select>
        </div>
        <div className="flex items-center gap-3">
          <span>© {new Date().getFullYear()} Aesthetic Engine Lab</span>
          <span>v0.2 preview</span>
        </div>
      </div>
    </footer>
  );
}
