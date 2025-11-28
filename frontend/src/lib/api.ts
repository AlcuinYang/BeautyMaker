import type {
  ApplicationDetail,
  ApplicationMeta,
  AestheticResponse,
  AestheticTaskPayload,
  PipelineResponse,
  ImageComposeResponse,
  ProviderListResponse,
  WorkItem,
  GalleryResponse,
} from "../types";

const API_BASE =
  import.meta.env.VITE_AE_API?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(
      `请求失败：${response.status} ${response.statusText} - ${message}`,
    );
  }
  return (await response.json()) as T;
}

export const api = {
  listApps: () => request<ApplicationMeta[]>("/api/apps"),
  getAppDetail: (id: string) => request<ApplicationDetail>(`/api/apps/${id}`),
  listWorks: () => request<WorkItem[]>("/api/works"),
  runAesthetic: (payload: AestheticTaskPayload) =>
    request<AestheticResponse>("/v1/aesthetic", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  publishWork: (payload: Record<string, unknown>) =>
    request<{ status: string; payload: Record<string, unknown> }>(
      "/v1/publish",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    ),
  listProviders: () =>
    request<ProviderListResponse>("/api/providers").then((data) => data.providers),
  runTextToImagePipeline: (payload: {
    prompt: string;
    providers: string[];
    num_candidates: number;
    reference_images?: string[];
    params: { ratio: string; expand_prompt: boolean };
  }) =>
    request<PipelineResponse>("/v1/pipeline/text2image", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  runImageComposePipeline: (payload: {
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
  }) =>
    request<ImageComposeResponse>("/v1/pipeline/image2image", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listGallery: (page = 1, pageSize = 9) =>
    request<GalleryResponse>(
      `/api/mock/gallery?page=${encodeURIComponent(page)}&page_size=${encodeURIComponent(
        pageSize,
      )}`,
    ),
};
