import React, { useEffect } from "react";
import { Link } from "react-router-dom";

const CameraIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
    <circle cx="12" cy="13" r="3" />
  </svg>
);

const SparklesIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1 -8.313 -12.454z" />
    <path d="M17 4a2 2 0 0 0 2 2a2 2 0 0 0 -2 2a2 2 0 0 0 -2 -2a2 2 0 0 0 2 -2" />
    <path d="M19 11h2m-1 -1v2" />
  </svg>
);

const ArrowRightIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={2}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M5 12h14" />
    <path d="M12 5l7 7-7 7" />
  </svg>
);

const tools = [
  {
    id: "img2img",
    title: "一拍即合 (Ecommerce Pro)",
    description: "上传产品照片，智能去底、光影重构。一键生成电商详情页大片，转化率倍增。",
    path: "/image-compose",
    icon: CameraIcon,
    theme: "purple",
  },
  {
    id: "txt2img",
    title: "最美图片 (Creative Studio)",
    description: "输入文字，生成高质量幻想图像与艺术作品。从构思到落地的极致体验。",
    path: "/generate",
    icon: SparklesIcon,
    theme: "cyan",
  },
] as const;

const LiquidCard = ({ tool }: { tool: (typeof tools)[0] }) => {
  const isPurple = tool.theme === "purple";

  return (
    <Link
      to={tool.path}
      className="group relative w-full h-[500px] 2xl:h-[600px] flex flex-col justify-end overflow-hidden rounded-[2.5rem] border border-white/10 bg-slate-900/80 backdrop-blur-2xl transition-all duration-500 hover:border-white/20 hover:shadow-2xl hover:shadow-cyan-500/10 hover:-translate-y-1"
    >
      <div
        className="absolute inset-0 z-0 opacity-20 pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      <div
        className={`pointer-events-none absolute -top-24 -right-24 w-96 h-96 rounded-full blur-[100px] opacity-20 transition-all duration-700 group-hover:scale-125 group-hover:opacity-50 ${
          isPurple ? "bg-purple-500" : "bg-blue-500"
        }`}
      />
      <div
        className={`pointer-events-none absolute -bottom-24 -left-24 w-80 h-80 rounded-full blur-[100px] opacity-20 transition-all duration-700 group-hover:scale-125 group-hover:opacity-50 ${
          isPurple ? "bg-pink-500" : "bg-cyan-500"
        }`}
      />

      <div
        className="absolute inset-0 opacity-20 z-0 pointer-events-none mix-blend-overlay"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='1'/%3E%3C/svg%3E\")",
        }}
      ></div>

      <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-transparent opacity-90 pointer-events-none" />

      <div className="relative z-10 p-10 2xl:p-14 flex flex-col h-full justify-between">
        <div className="relative group/icon">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-white/10 to-white/0 border border-white/20 flex items-center justify-center backdrop-blur-md shadow-lg shadow-black/20 group-hover:bg-white/15 transition-all duration-300">
            <div
              className={`absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-xl ${
                isPurple ? "bg-purple-500/20" : "bg-cyan-500/20"
              }`}
            />
            <tool.icon className="relative z-10 w-10 h-10 text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.3)]" />
          </div>
        </div>

        <div className="translate-y-2 group-hover:translate-y-0 transition-transform duration-500">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-4xl 2xl:text-5xl font-bold text-white tracking-tight drop-shadow-lg">
              {tool.title}
            </h3>
            <div className="w-14 h-14 rounded-full bg-white flex items-center justify-center text-slate-950 opacity-0 -translate-x-8 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-500 shadow-[0_0_20px_rgba(255,255,255,0.4)]">
              <ArrowRightIcon className="w-6 h-6 stroke-[2.5px]" />
            </div>
          </div>

          <p className="text-lg 2xl:text-xl text-slate-300 font-light leading-relaxed max-w-lg border-l-2 border-white/20 pl-4">
            {tool.description}
          </p>
        </div>
      </div>
    </Link>
  );
};

export default function AiApplicationPage() {
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-white selection:bg-cyan-500/30">
      <div className="relative w-full flex flex-col items-center justify-center pt-24 pb-12 2xl:pt-32 2xl:pb-16 overflow-hidden min-h-[45vh] 2xl:min-h-[40vh]">
        <div className="absolute top-[-20%] left-[20%] w-[600px] h-[600px] 2xl:w-[1200px] 2xl:h-[1200px] bg-purple-900/20 rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute bottom-[-10%] right-[20%] w-[500px] h-[500px] 2xl:w-[1000px] 2xl:h-[1000px] bg-cyan-900/20 rounded-full blur-[100px] pointer-events-none" />

        <div className="relative z-10 flex flex-col items-center px-4 max-w-5xl mx-auto text-center">
          <div className="mb-6 2xl:mb-8 px-5 py-2 rounded-full border border-white/10 bg-white/5 backdrop-blur-md">
            <span className="text-xs 2xl:text-sm font-bold tracking-[0.2em] text-white/70 uppercase">
              Aesthetic Engine Playground
            </span>
          </div>

          <h1 className="text-6xl md:text-7xl 2xl:text-9xl font-bold tracking-tight text-white mb-6 2xl:mb-10 drop-shadow-2xl">
            多模型一站式 <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-200 to-slate-400">
              AI 创作中心
            </span>
          </h1>

          <p className="text-xl md:text-2xl 2xl:text-3xl text-slate-400 max-w-2xl 2xl:max-w-4xl mx-auto mb-8 2xl:mb-12 leading-relaxed font-light">
            重构电商美学，让 AI 更懂商业摄影。
          </p>
        </div>
      </div>

      <div className="relative z-10 max-w-7xl 2xl:max-w-[1600px] mx-auto px-6 pb-20 2xl:pb-32">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 2xl:gap-12">
          {tools.map((tool) => (
            <LiquidCard key={tool.id} tool={tool} />
          ))}
        </div>
      </div>
    </div>
  );
}
