import { useCallback, useState } from "react";
import { api } from "../lib/api";
import type { ImageComposeResponse } from "../types";

export const ComposeStage = {
  Idle: 0,
  Uploading: 1,
  Generating: 2,
  Verifying: 3,
  Completed: 4,
} as const;

export type ComposeStageValue = (typeof ComposeStage)[keyof typeof ComposeStage];

type ComposePayload = {
  prompt: string;
  reference_images: string[];
  providers: string[];
  size: string;
  params: {
    num_variations?: number;
    image_size?: string;
    group_mode?: boolean;
    category?: "standing" | "flat" | "other";
    use_auto_segmentation?: boolean;
  };
};

export function useImageCompose() {
  const [stage, setStage] = useState<ComposeStageValue>(ComposeStage.Idle);
  const [result, setResult] = useState<ImageComposeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const run = useCallback(async (payload: ComposePayload) => {
    if (!payload.prompt.trim()) {
      setError("请输入提示词。");
      return;
    }
    if (!payload.reference_images.length) {
      setError("请至少上传一张产品图片。");
      return;
    }
    setIsRunning(true);
    setError(null);
    setResult(null);
    setStage(ComposeStage.Uploading);

    try {
      await new Promise((resolve) => setTimeout(resolve, 200));
      setStage(ComposeStage.Generating);

      const response = await api.runImageComposePipeline(payload);

      if (response.status !== "success") {
        throw new Error(response.message ?? "生成失败，请稍后重试");
      }

      setStage(ComposeStage.Verifying);
      await new Promise((resolve) => setTimeout(resolve, 200));
      setStage(ComposeStage.Completed);
      setResult(response);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "生成失败，请稍后重试");
      setStage(ComposeStage.Idle);
    } finally {
      setIsRunning(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setStage(ComposeStage.Idle);
  }, []);

  return { stage, result, error, isRunning, run, reset };
}
