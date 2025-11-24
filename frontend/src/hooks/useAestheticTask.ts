import { useCallback, useState } from "react";
import { api } from "../lib/api";
import type { AestheticTaskPayload, AestheticTaskState } from "../types";

const initialState: AestheticTaskState = {
  isLoading: false,
  error: null,
  result: null,
};

export function useAestheticTask() {
  const [state, setState] = useState<AestheticTaskState>(initialState);

  const runTask = useCallback(async (payload: AestheticTaskPayload) => {
    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      const response = await api.runAesthetic(payload);
      setState({
        isLoading: false,
        error: null,
        result: response,
      });
      return response;
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "调用美学引擎失败，请稍后再试";
      setState({
        isLoading: false,
        error: message,
        result: null,
      });
      throw error;
    }
  }, []);

  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  return {
    state,
    runTask,
    reset,
  };
}
