import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { ParameterPanel, type ParameterPanelSubmit } from "../../components/ParameterPanel";
import { ResultViewer } from "../../components/ResultViewer";
import { api } from "../../lib/api";
import { useAestheticTask } from "../../hooks/useAestheticTask";
import type {
  ApplicationDetail,
  ModuleToggleOption,
} from "../../types";

const MODULE_NAME_MAP: Record<string, string> = {
  color_score: "光色表现",
  contrast_score: "构图表达",
  clarity_eval: "清晰完整度",
  noise_eval: "风格协调性",
  quality_score: "情绪感染力",
  holistic: "综合美感",
};

const SIZE_PRESET: Record<string, string> = {
  "1:1": "1024x1024",
  "3:4": "768x1024",
  "9:16": "768x1365",
};

export default function AiDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [detail, setDetail] = useState<ApplicationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);
  const { state, runTask } = useAestheticTask();

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setPageError(null);
    api
      .getAppDetail(id)
      .then((data) => {
        setDetail({
          meta: data.meta ?? null,
          template: data.template,
        });
      })
      .catch((error) => {
        console.error(error);
        setPageError(
          error instanceof Error ? error.message : "加载应用失败，请稍后重试。",
        );
      })
      .finally(() => setLoading(false));
  }, [id]);

  const moduleOptions: ModuleToggleOption[] = useMemo(() => {
    if (!detail?.template) return [];
    if (detail.template.module_options?.length) {
      return detail.template.module_options;
    }
    if (detail.meta?.modules?.length) {
      return detail.meta.modules.map((key) => ({
        key,
        label: MODULE_NAME_MAP[key] ?? key,
      }));
    }
    return [
      { key: "color_score", label: MODULE_NAME_MAP.color_score },
      { key: "contrast_score", label: MODULE_NAME_MAP.contrast_score },
      { key: "clarity_eval", label: MODULE_NAME_MAP.clarity_eval },
      { key: "noise_eval", label: MODULE_NAME_MAP.noise_eval },
      { key: "quality_score", label: MODULE_NAME_MAP.quality_score },
    ];
  }, [detail]);

  const moduleNameMap = useMemo(() => {
    const map: Record<string, string> = { ...MODULE_NAME_MAP };
    for (const option of moduleOptions) {
      map[option.key] = option.label ?? option.key;
    }
    return map;
  }, [moduleOptions]);

  const handleRun = async (values: ParameterPanelSubmit) => {
    if (!detail) return;

    const modules =
      values.enableAesthetic && values.selectedModules.length > 0
        ? values.selectedModules
        : [];

    const payload = {
      task: "text2image",
      prompt:
        values.prompt.length > 0
          ? values.prompt
          : detail.template.default_params?.prompt?.toString() ??
            "Aesthetic Engine Playground prompt",
      provider: detail.meta?.id ?? detail.template.id,
      size: SIZE_PRESET[values.aspectRatio] ?? "1024x1024",
      use_modules: modules.length > 0 ? modules : moduleOptions.map((item) => item.key),
      params: {
        num_outputs: values.outputCount,
        aspect_ratio: values.aspectRatio,
        prompt_mode: values.promptMode,
        style: detail.template.default_params?.style ?? "cinematic",
      },
      enhancement: {
        apply_clarity: values.applyClarity,
      },
    };

    try {
      await runTask(payload);
    } catch {
      // runTask already设置错误 state
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#07070a] text-slate-400">
        正在加载应用配置...
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#07070a] text-slate-400">
        {pageError ?? "找不到指定的应用。"}
      </div>
    );
  }

  const { meta, template } = detail;

  return (
    <div className="min-h-screen bg-[#050508] pb-20 pt-16 text-white">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 md:px-10">
        <motion.header
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-white/5 via-white/10 to-emerald-500/10 p-8 backdrop-blur-2xl"
        >
          <div className="flex flex-col gap-6 md:flex-row md:items-center">
            {meta?.cover ? (
              <div className="overflow-hidden rounded-2xl border border-white/10 bg-black/20">
                <motion.img
                  src={meta.cover}
                  alt={template.name}
                  className="h-32 w-48 object-cover"
                  initial={{ scale: 1.04 }}
                  animate={{ scale: 1 }}
                  transition={{ duration: 0.9, ease: "easeOut" }}
                />
              </div>
            ) : null}
            <div className="space-y-4">
              <div className="inline-flex w-fit items-center gap-2 rounded-full border border-white/15 bg-black/30 px-4 py-1 text-xs uppercase tracking-[0.3em] text-slate-300">
                {meta?.title ?? template.name}
              </div>
              <h1 className="text-4xl font-semibold tracking-tight text-white md:text-5xl">
                {template.name}
              </h1>
              <p className="max-w-3xl text-sm leading-relaxed text-slate-300 md:text-base">
                {template.description}
              </p>

              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                {meta?.tags?.map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full border border-white/10 bg-black/30 px-3 py-1"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </motion.header>

        {pageError && (
          <div className="rounded-3xl border border-rose-400/40 bg-rose-500/10 p-4 text-sm text-rose-200">
            {pageError}
          </div>
        )}

        <div className="grid gap-8 lg:grid-cols-[0.95fr_1.05fr]">
          <ParameterPanel
            template={template}
            moduleOptions={moduleOptions}
            defaultPrompt={template.default_params?.prompt?.toString()}
            isSubmitting={state.isLoading}
            errorMessage={state.error}
            onRun={handleRun}
          />

          <ResultViewer
            result={state.result}
            isLoading={state.isLoading}
            moduleNameMap={moduleNameMap}
          />
        </div>

        <section className="rounded-3xl border border-white/10 bg-white/5 p-6 text-sm text-slate-300 backdrop-blur-xl">
          <h2 className="text-base font-semibold text-white">用户作品广场 · 即将上线</h2>
          <p className="mt-2 text-sm text-slate-400">
            未来将在此展示相关作品流、评论与复现配置，支持一键复现他人参数。
          </p>
        </section>
      </div>
    </div>
  );
}
