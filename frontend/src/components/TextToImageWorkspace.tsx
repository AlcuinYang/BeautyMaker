import { useCallback, useEffect, useMemo, useState } from "react";
import { GenerateHeader } from "./GenerateHeader";
import { PromptPanel } from "./PromptPanel";
import { GenerateResult } from "./GenerateResult";
import { usePipeline } from "../hooks/usePipeline";
import { api } from "../lib/api";
import type { PipelineResponse, ProviderInfo } from "../types";

export function TextToImageWorkspace() {
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [providersLoading, setProvidersLoading] = useState(true);
  const [selectedProviders, setSelectedProviders] = useState<string[]>([]);

  const [prompt, setPrompt] = useState("薄雾清晨中的未来城市，阳光穿透玻璃穹顶");
  const [numCandidates, setNumCandidates] = useState(3);
  const [ratio, setRatio] = useState("1:1");
  const [formError, setFormError] = useState<string | null>(null);
  const [referenceImage, setReferenceImage] = useState<string | null>(null);

  const { stage, result, error, isRunning, runPipeline, reset } = usePipeline();

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = window.localStorage.getItem("ae_selected_providers");
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          if (Array.isArray(parsed) && parsed.length > 0) {
            setSelectedProviders(parsed.filter((item): item is string => typeof item === "string"));
          }
        } catch (error) {
          console.warn("读取缓存的模型选择失败", error);
        }
      }
    }

    let mounted = true;
    setProvidersLoading(true);
    api
      .listProviders()
      .then((data) => {
        if (!mounted) return;

        const allowedIds = new Set(["qwen", "dalle", "nano_banana"]);
        const filtered = data.filter((item) => allowedIds.has(item.id));

        const doubaoProvider: ProviderInfo = {
          id: "doubao_seedream",
          display_name: "豆包 · Seedream",
          description: "ByteDance Doubao Seedream 文生图模型。",
          category: "image_generation",
          is_free: false,
          is_active: true,
          icon: null,
          endpoint: "https://www.doubao.com/seeds/dream",
          latency_ms: null,
        };

        if (!filtered.some((item) => item.id === doubaoProvider.id)) {
          filtered.push(doubaoProvider);
        }

        setProviders(filtered);

        setSelectedProviders((current) => {
          const validCurrent = current.filter((id) => filtered.some((item) => item.id === id));
          if (validCurrent.length > 0) {
            return validCurrent;
          }
          const defaultProvider = filtered.find((item) => item.id === "qwen") ?? filtered[0];
          return defaultProvider ? [defaultProvider.id] : [];
        });
      })
      .catch((err) => {
        console.error("加载模型列表失败", err);
      })
      .finally(() => mounted && setProvidersLoading(false));
    return () => {
      mounted = false;
    };
  }, []);

  const providerMap = useMemo(() => {
    const map: Record<string, ProviderInfo> = {};
    providers.forEach((provider) => {
      map[provider.id] = provider;
    });
    return map;
  }, [providers]);

  const handleAddProvider = useCallback(
    (id: string) => {
      setSelectedProviders((current) => {
        if (current.includes(id)) {
          return current;
        }
        return [...current, id];
      });
    },
    [],
  );

  const handleRemoveProvider = useCallback(
    (id: string) => {
      setSelectedProviders((current) => current.filter((item) => item !== id));
    },
    [],
  );

  useEffect(() => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(
        "ae_selected_providers",
        JSON.stringify(selectedProviders),
      );
    }
  }, [selectedProviders]);

  const handleRun = useCallback(async () => {
    if (!prompt.trim()) {
      setFormError("请输入提示词。");
      return;
    }
    if (selectedProviders.length === 0) {
      setFormError("请至少选择一个模型。");
      return;
    }
    setFormError(null);
    runPipeline({
      prompt,
      providers: selectedProviders,
      num_candidates: numCandidates,
      params: {
        ratio,
        expand_prompt: false,
        reference_image: referenceImage ?? undefined,
      },
    });
  }, [selectedProviders, runPipeline, prompt, numCandidates, ratio, referenceImage]);

  const handleRegenerate = useCallback(() => {
    reset();
    handleRun();
  }, [reset, handleRun]);

  const handleReferenceUpload = useCallback((file: File) => {
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        setReferenceImage(reader.result);
      }
    };
    reader.onerror = () => {
      console.warn("读取参考图片失败");
    };
    reader.readAsDataURL(file);
  }, []);

  const handleReferenceRemove = useCallback(() => {
    setReferenceImage(null);
  }, []);

  return (
    <div className="flex flex-col gap-6 px-4 pb-12 pt-6 md:px-8 lg:px-12">
      <GenerateHeader />

      <div className="flex flex-col gap-6">
        <PromptPanel
              prompt={prompt}
              onPromptChange={setPrompt}
              referenceImage={referenceImage}
              onReferenceUpload={handleReferenceUpload}
              onReferenceRemove={handleReferenceRemove}
              numCandidates={numCandidates}
              onNumCandidatesChange={setNumCandidates}
              ratio={ratio}
              onRatioChange={setRatio}
              providers={providers}
              providerMap={providerMap}
              providersLoading={providersLoading}
              selectedProviders={selectedProviders}
              onAddProvider={handleAddProvider}
          onRemoveProvider={handleRemoveProvider}
          onSubmit={handleRun}
          disabled={isRunning}
        />

        {(error || formError) && (
          <div className="rounded-3xl border border-rose-400/40 bg-rose-500/10 p-4 text-sm text-rose-200">
            {formError ?? error}
          </div>
        )}

        <div className="rounded-3xl border border-white/10 bg-white/5/80 p-2 backdrop-blur-xl">
          <GenerateResult
            result={result as PipelineResponse | null}
            onRegenerate={handleRegenerate}
            stage={stage}
            disabled={isRunning}
            providerMap={providerMap}
          />
        </div>
      </div>
    </div>
  );
}
