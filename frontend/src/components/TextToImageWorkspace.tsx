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

  const [prompt, setPrompt] = useState("星际穿越，黑洞，黑洞里冲出一辆快支离破碎的复古列车，抢视觉冲击力，电影大片，末日既视感，动感，对比色，oc渲染，光线追踪，动态模糊，景深，超现实主义，深蓝，画面通过细腻的丰富的色彩层次塑造主体与场景，质感真实，暗黑风背景的光影效果营造出氛围，整体兼具艺术幻想感，夸张的广角透视效果，耀光，反射，极致的光影，强引力，吞噬");
  const [numCandidates, setNumCandidates] = useState(3);
  const [ratio, setRatio] = useState("1:1");
  const [formError, setFormError] = useState<string | null>(null);
  const [referenceImages, setReferenceImages] = useState<string[]>([]);
  const [aestheticModel, setAestheticModel] = useState("mnet_v1");

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

        const allowedIds = new Set(["wan", "doubao_seedream"]);
        const filtered = data.filter((item) => allowedIds.has(item.id));

        const fallbackProviders: ProviderInfo[] = [
          {
            id: "wan",
            display_name: "Tongyi Wanxiang (Wan)",
            description: "阿里通义万相图生图",
            category: "image_generation",
            is_free: false,
            is_active: true,
            icon: null,
            endpoint: "",
            latency_ms: null,
          },
          {
            id: "doubao_seedream",
            display_name: "豆包 · Seedream",
            description: "ByteDance Doubao Seedream 文生图模型。",
            category: "image_generation",
            is_free: false,
            is_active: true,
            icon: null,
            endpoint: "https://www.doubao.com/seeds/dream",
            latency_ms: null,
          },
        ];

        const mergedMap: Record<string, ProviderInfo> = {};
        [...filtered, ...fallbackProviders].forEach((item) => {
          if (allowedIds.has(item.id)) {
            mergedMap[item.id] = item;
          }
        });

        const mergedProviders = Object.values(mergedMap);
        setProviders(mergedProviders);

        setSelectedProviders((current) => {
          const validCurrent = current.filter((id) => mergedProviders.some((item) => item.id === id));
          if (validCurrent.length > 0) {
            return validCurrent;
          }
          const defaultProvider =
            mergedProviders.find((item) => item.id === "wan") ??
            mergedProviders.find((item) => item.id === "doubao_seedream") ??
            mergedProviders[0];
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
      reference_images: referenceImages.length > 0 ? referenceImages : undefined,
      params: {
        ratio,
        expand_prompt: false,
      },
    });
  }, [selectedProviders, runPipeline, prompt, numCandidates, ratio, referenceImages]);

  const handleRegenerate = useCallback(() => {
    reset();
    handleRun();
  }, [reset, handleRun]);

  const handleReferenceUpload = useCallback((file: File) => {
    if (referenceImages.length >= 10) {
      setFormError("最多只能上传10张参考图片");
      return;
    }
    const allowedTypes = new Set(["image/png", "image/jpeg"]);
    if (!allowedTypes.has(file.type)) {
      setFormError("仅支持上传 PNG 或 JPEG 图片，请重新选择。");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        setReferenceImages((prev) => [...prev, reader.result as string]);
        setFormError(null);
      }
    };
    reader.onerror = () => {
      console.warn("读取参考图片失败");
      setFormError("读取参考图片失败，请重试");
    };
    reader.readAsDataURL(file);
  }, [referenceImages.length]);

  const handleReferenceDrop = useCallback((files: File[]) => {
    if (files.length === 0) return;
    for (const file of files) {
      if (referenceImages.length >= 10) break;
      handleReferenceUpload(file);
    }
  }, [handleReferenceUpload, referenceImages.length]);

  const handleReferenceRemove = useCallback((index: number) => {
    setReferenceImages((prev) => prev.filter((_, i) => i !== index));
  }, []);

  return (
    <div className="flex flex-col gap-6 px-4 pb-12 pt-6 md:px-8 lg:px-12">
      <GenerateHeader />

      <div className="flex flex-col gap-6">
        <PromptPanel
          prompt={prompt}
          onPromptChange={setPrompt}
          referenceImages={referenceImages}
          onReferenceUpload={handleReferenceUpload}
          onReferenceDrop={handleReferenceDrop}
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
          aestheticModel={aestheticModel}
          onAestheticModelChange={setAestheticModel}
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
