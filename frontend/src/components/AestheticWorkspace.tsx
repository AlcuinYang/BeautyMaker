import { useCallback, useEffect, useRef, useState } from "react";
import { AestheticHeader } from "./core/AestheticHeader";
import { AestheticFooter } from "./core/AestheticFooter";
import { AestheticPromptPanel } from "./core/AestheticPromptPanel";
import { AestheticGallery } from "./core/AestheticGallery";
import { AestheticHeroPreview } from "./core/AestheticHeroPreview";
import { DEFAULT_PROMPT } from "./registry/aestheticOptions";

export function AestheticWorkspace() {
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT);
  const [ratio, setRatio] = useState("3:4");
  const [count, setCount] = useState(3);
  const [isRunning, setIsRunning] = useState(false);
  const timerRef = useRef<number | null>(null);

  const handleRun = useCallback(() => {
    if (isRunning) return;
    setIsRunning(true);
    if (timerRef.current) {
      window.clearTimeout(timerRef.current);
    }
    timerRef.current = window.setTimeout(() => {
      setIsRunning(false);
      timerRef.current = null;
    }, 1200);
  }, [isRunning]);

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        window.clearTimeout(timerRef.current);
      }
    };
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-br from-[#06070c] via-[#0c101a] to-[#141824] text-white">
      <AestheticHeader />
      <main className="flex flex-1 flex-col overflow-hidden">
        <div className="mx-auto flex w-full max-w-[1600px] flex-1 flex-col gap-6 px-6 py-8 md:px-10">
          <div className="flex flex-1 flex-col gap-6 lg:flex-row">
            <aside className="w-full lg:w-[32%] xl:w-[30%]">
              <AestheticPromptPanel
                prompt={prompt}
                onPromptChange={setPrompt}
                ratio={ratio}
                onRatioChange={setRatio}
                count={count}
                onCountChange={setCount}
                onRun={handleRun}
                isRunning={isRunning}
              />
            </aside>
            <section className="flex w-full flex-1 flex-col gap-6">
              <AestheticHeroPreview />
              <AestheticGallery />
            </section>
          </div>
        </div>
      </main>
      <AestheticFooter />
    </div>
  );
}
