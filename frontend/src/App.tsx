import { BrowserRouter, Link, Navigate, Route, Routes } from "react-router-dom";
import AiApplicationPage from "./pages/ai-application";
import AiDetailPage from "./pages/ai-detail/[id]";
import ModelSelectorPage from "./pages/model-selector";
import GeneratePage from "./pages/generate";
import ImageComposePage from "./pages/image-compose";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#050509] text-white">
        <header className="border-b border-white/10 bg-black/30 backdrop-blur-xl">
          <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4 md:px-10 md:py-5">
            <Link
              to="/ai-application"
              className="text-lg font-semibold tracking-wide text-white"
            >
              Aesthetic Engine Playground
            </Link>
            <nav className="flex items-center gap-6 text-sm text-slate-400">
              <Link to="/ai-application" className="transition hover:text-emerald-300">
                应用广场
              </Link>
              <Link to="/profile" className="transition hover:text-emerald-300">
                个人中心
              </Link>
            </nav>
          </div>
        </header>

        <Routes>
          <Route path="/" element={<Navigate to="/ai-application" replace />} />
          <Route path="/ai-application" element={<AiApplicationPage />} />
          <Route path="/model-selector" element={<ModelSelectorPage />} />
          <Route path="/generate" element={<GeneratePage />} />
          <Route path="/image-compose" element={<ImageComposePage />} />
          <Route path="/ai-detail/:id" element={<AiDetailPage />} />
          <Route
            path="*"
            element={
              <div className="flex min-h-[60vh] items-center justify-center text-slate-400">
                页面建设中，敬请期待。
              </div>
            }
          />
        </Routes>

        <footer className="border-t border-white/10 bg-black/30 text-sm text-slate-500">
          <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5 md:px-10">
            <span>© {new Date().getFullYear()} Aesthetic Engine Lab</span>
            <span>下一步：作品市场 · 会员体系</span>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}

export default App;
