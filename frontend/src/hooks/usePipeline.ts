import { useCallback, useState } from "react";
import { api } from "../lib/api";
import type { PipelineResponse } from "../types";

type PipelinePayload = {
  prompt: string;
  providers: string[];
  num_candidates: number;
  reference_images?: string[];
  params: {
    ratio: string;
    expand_prompt: boolean;
  };
};

export const PipelineStage = {
  Idle: 0,
  ExpandingPrompt: 1,
  Generating: 2,
  Scoring: 3,
  Completed: 4,
} as const;

export type PipelineStageValue = (typeof PipelineStage)[keyof typeof PipelineStage];

export function usePipeline() {
  const [stage, setStage] = useState<PipelineStageValue>(PipelineStage.Idle);
  const [result, setResult] = useState<PipelineResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const runPipeline = useCallback(async (payload: PipelinePayload) => {
    setIsRunning(true);
    setError(null);
    setResult(null);
    setStage(PipelineStage.ExpandingPrompt);

    try {
      await new Promise((resolve) => setTimeout(resolve, 300));
      setStage(PipelineStage.Generating);

      const response = await api.runTextToImagePipeline(payload);

      setStage(PipelineStage.Scoring);

      if (response.status !== "success") {
        throw new Error(response.summary ?? response.message ?? "生成失败，请稍后重试");
      }

      setStage(PipelineStage.Completed);

      setResult(response);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "管线执行失败");
      setStage(PipelineStage.Idle);
    } finally {
      setIsRunning(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setStage(PipelineStage.Idle);
  }, []);

  return { stage, result, error, isRunning, runPipeline, reset };
}
