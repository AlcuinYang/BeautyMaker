export interface ApplicationMeta {
  id: string;
  slug?: string;
  title: string;
  author: string;
  cover: string;
  desc: string;
  tags: string[];
  likes?: number;
  views?: number;
  category?: string;
  modules?: string[];
}

export type ParameterSchema =
  | {
      key: string;
      type: "textarea";
      label: string;
      placeholder?: string;
    }
  | {
      key: string;
      type: "select";
      label: string;
      options: { label: string; value: string }[];
    }
  | {
      key: string;
      type: "slider";
      label: string;
      min: number;
      max: number;
      step?: number;
    }
  | {
      key: string;
      type: "toggle";
      label: string;
      default?: boolean;
    }
  | {
      key: string;
      type: "image_upload";
      label: string;
    };

export interface ModuleToggleOption {
  key: string;
  label: string;
  description?: string;
}

export interface ApplicationTemplate {
  id: string;
  name: string;
  description: string;
  default_params: Record<string, unknown>;
  param_schema: ParameterSchema[];
  module_options?: ModuleToggleOption[];
}

export interface ApplicationDetail {
  meta: ApplicationMeta | null;
  template: ApplicationTemplate;
}

export interface AestheticScores {
  [module: string]: number | undefined;
  composite_score?: number;
}

export interface AestheticResponse {
  status: string;
  image_url: string;
  images?: string[];
  scores: Record<string, number>;
  composite_score?: number;
  metadata?: Record<string, unknown>;
  best_candidate?: string;
  modules_used?: string[];
  message?: string;
  task_id?: string;
}

export interface WorkItem {
  id: string;
  thumbnail: string;
  title: string;
  score: number;
  module_summary: Record<string, number>;
  app_id: string;
  author: {
    id: string;
    name: string;
    avatar?: string;
  };
  created_at: string;
}

export interface AestheticTaskPayload {
  task: string;
  prompt: string;
  provider: string;
  size: string;
  use_modules: string[];
  params: Record<string, unknown>;
  enhancement: {
    apply_clarity: boolean;
  };
}

export interface AestheticTaskState {
  isLoading: boolean;
  error: string | null;
  result: AestheticResponse | null;
}

export interface ProviderInfo {
  id: string;
  display_name: string;
  description: string;
  category: string;
  is_free: boolean;
  is_active: boolean;
  icon?: string | null;
  endpoint?: string | null;
  latency_ms?: number | null;
}

export interface ProviderListResponse {
  status: string;
  providers: ProviderInfo[];
}

export interface PipelineCandidate {
  image_url: string;
  composite_score?: number;
  scores?: Record<string, number>;
  provider?: string;
}

export interface PipelinePromptInfo {
  original: string;
  applied: string;
  expanded?: string | null;
  expansion_suffix?: string | null;
}

export interface PipelineResponse {
  status: string;
  best_image_url?: string;
  candidates?: PipelineCandidate[];
  best_composite_score?: number;
  review?: {
    title?: string;
    analysis?: string;
    key_difference?: string;
  };
  summary?: string;
  prompt?: PipelinePromptInfo;
  providers_used?: string[];
  message?: string;
}

export interface ImageComposeResultItem {
  provider: string;
  image_url: string;
  scores?: Record<string, number>;
  composite_score?: number;
  sequence_index?: number | null;
  group_size?: number | null;
  verification?: {
    status?: string;
    score?: number;
    comment?: string;
  } | null;
}

export interface ImageComposeResponse {
  status: string;
  task_id?: string;
  best_image_url?: string;
  best_provider?: string;
  results: ImageComposeResultItem[];
  reference_images: string[];
  image_size?: string;
  providers_used?: string[];
  group_mode?: boolean;
  message?: string;
  aesthetic_score?: number;
  review?: {
    title: string;
    analysis: string;
    key_difference: string;
  };
}

export interface GalleryItem {
  id: string;
  title: string;
  image_url: string;
  likes: number;
  comments: number;
  author: string;
  tags?: string[];
  created_at: string;
}

export interface GalleryResponse {
  page: number;
  page_size: number;
  has_more: boolean;
  items: GalleryItem[];
  total: number;
}
