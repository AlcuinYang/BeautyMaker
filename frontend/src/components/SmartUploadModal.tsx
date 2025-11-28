import { AnimatePresence, motion } from "framer-motion";
import type { ChangeEvent, DragEvent } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "./ui/Button";
import { cn } from "../utils/cn";

type UploadCategory = "standing" | "flat";

interface SmartUploadModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (file: File, category: UploadCategory) => void;
}

const stepVariants = {
  initial: { opacity: 0, y: 12, scale: 0.98 },
  animate: { opacity: 1, y: 0, scale: 1 },
  exit: { opacity: 0, y: -10, scale: 0.98 },
};

export function SmartUploadModal({ open, onClose, onConfirm }: SmartUploadModalProps) {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [category, setCategory] = useState<UploadCategory | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (!open) {
      setStep(1);
      setCategory(null);
      setFile(null);
      setPreviewUrl(null);
    }
  }, [open]);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const guideText = useMemo(() => {
    if (category === "standing") {
      return "📸 拍摄秘籍: 请平视拍摄 (Eye-level)。请使用白纸背景。不要手持。";
    }
    if (category === "flat") {
      return "📸 拍摄秘籍: 请垂直俯拍 (Top-down)。请平铺在纯色背景上。";
    }
    return "选择产品类别以获取最佳拍摄指导。";
  }, [category]);

  const handleSelectCategory = (value: UploadCategory) => {
    setCategory(value);
    setStep(2);
  };

  const applyFile = (nextFile: File | null) => {
    if (!nextFile) {
      return;
    }
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setFile(nextFile);
    setPreviewUrl(URL.createObjectURL(nextFile));
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    applyFile(event.target.files?.[0] ?? null);
  };

  const handleDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
    const droppedFile = event.dataTransfer?.files?.[0];
    applyFile(droppedFile ?? null);
  };

  const handleDragOver = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
  };

  const triggerFileDialog = () => {
    fileInputRef.current?.click();
  };

  const handleConfirm = () => {
    if (file && category) {
      onConfirm(file, category);
      onClose();
    }
  };

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.18, ease: "easeOut" }}
        className="relative w-[90vw] max-w-3xl rounded-3xl border border-white/10 bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 p-6 shadow-2xl shadow-emerald-500/15"
      >
        <div className="flex items-center justify-between pb-4">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-emerald-300/70">Smart Upload</p>
            <h2 className="mt-1 text-xl font-semibold text-white">电商拍摄向导</h2>
            <p className="text-sm text-slate-300/80">根据品类给出拍摄 SOP，提升生成效果。</p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            关闭
          </Button>
        </div>

        <div className="mb-6 flex items-center space-x-2 text-xs font-medium text-slate-200/70">
          {[1, 2, 3].map((current) => (
            <div key={current} className="flex items-center space-x-2">
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full border text-sm",
                  current === step
                    ? "border-emerald-400/80 bg-emerald-400/15 text-white"
                    : current < step
                      ? "border-emerald-300/70 bg-emerald-300/10 text-emerald-100"
                      : "border-white/15 bg-white/5 text-slate-200/80",
                )}
              >
                {current}
              </div>
              {current < 3 && <div className="h-[1px] w-12 bg-gradient-to-r from-emerald-400/60 via-white/20 to-transparent" />}
            </div>
          ))}
        </div>

        <div className="relative min-h-[280px] overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-4">
          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div
                key="step-1"
                variants={stepVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                transition={{ duration: 0.2, ease: "easeOut" }}
                className="grid grid-cols-1 gap-4 md:grid-cols-2"
              >
                <CategoryCard
                  title="立体产品"
                  subtitle="化妆品 / 手办 / 小摆件"
                  emoji="🧴"
                  active={category === "standing"}
                  onClick={() => handleSelectCategory("standing")}
                />
                <CategoryCard
                  title="扁平产品"
                  subtitle="服饰 / 书本 / 画作"
                  emoji="👕"
                  active={category === "flat"}
                  onClick={() => handleSelectCategory("flat")}
                />
              </motion.div>
            )}

            {step === 2 && (
              <motion.div
                key="step-2"
                variants={stepVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                transition={{ duration: 0.2, ease: "easeOut" }}
                className="flex h-full flex-col justify-between space-y-6"
              >
                <div className="space-y-3">
                  <p className="text-sm text-emerald-300/80">拍摄指导</p>
                  <p className="rounded-xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-base text-emerald-50">
                    {guideText}
                  </p>
                  <p className="text-xs text-slate-300/80">
                    贴士：保持光线均匀、避免反光与遮挡，图片越干净，抠图和生成效果越好。
                  </p>
                </div>
                <div className="flex items-center justify-between">
                  <Button variant="secondary" onClick={() => setStep(1)}>
                    上一步
                  </Button>
                  <Button
                    onClick={() => setStep(3)}
                    disabled={!category}
                    className="px-6"
                  >
                    我准备好了，开始上传
                  </Button>
                </div>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div
                key="step-3"
                variants={stepVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                transition={{ duration: 0.2, ease: "easeOut" }}
                className="flex h-full flex-col space-y-4"
              >
                <div className="rounded-xl border border-white/10 bg-slate-900/60 p-4">
                  <label
                    htmlFor="smart-upload"
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    className={cn(
                      "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-white/15 bg-white/5 p-6 text-center transition",
                      isDragging ? "border-emerald-400/60 bg-emerald-400/5" : "hover:border-emerald-400/50 hover:bg-white/10",
                    )}
                  >
                    <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-400/10 text-2xl">
                      📤
                    </div>
                    <div>
                      <p className="text-base font-medium text-white">上传参考图</p>
                      <p className="text-xs text-slate-300/80">支持 JPG / PNG，清晰无遮挡更佳</p>
                    </div>
                    <input
                      id="smart-upload"
                      type="file"
                      accept="image/*"
                      onChange={handleFileChange}
                      ref={fileInputRef}
                      className="hidden"
                    />
                    <Button variant="secondary" size="sm" type="button" onClick={triggerFileDialog}>
                      选择文件
                    </Button>
                  </label>
                </div>

                {previewUrl && (
                  <div className="flex items-center gap-4 rounded-xl border border-white/10 bg-white/5 p-3">
                    <img
                      src={previewUrl}
                      alt="上传预览"
                      className="h-20 w-20 rounded-lg object-cover"
                    />
                    <div className="flex flex-1 flex-col">
                      <p className="text-sm font-medium text-white">{file?.name}</p>
                      <p className="text-xs text-slate-300/80">
                        {category === "standing" ? "立体产品" : category === "flat" ? "扁平产品" : "未选择品类"}
                      </p>
                    </div>
                    <Button
                      variant="primary"
                      size="sm"
                      disabled={!file || !category}
                      onClick={handleConfirm}
                    >
                      确认并继续
                    </Button>
                  </div>
                )}

                {!previewUrl && (
                  <p className="text-xs text-slate-400">完成上传后，将自动应用抠图与质量控制。</p>
                )}

                <div className="flex justify-between pt-2">
                  <Button variant="secondary" onClick={() => setStep(2)}>
                    上一步
                  </Button>
                  <Button variant="ghost" onClick={onClose}>
                    取消
                  </Button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
}

interface CategoryCardProps {
  title: string;
  subtitle: string;
  emoji: string;
  active: boolean;
  onClick: () => void;
}

function CategoryCard({ title, subtitle, emoji, active, onClick }: CategoryCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "group flex h-full flex-col justify-between rounded-2xl border bg-white/5 p-5 text-left transition",
        active
          ? "border-emerald-400/70 bg-emerald-400/10 shadow-lg shadow-emerald-500/10"
          : "border-white/10 hover:border-emerald-400/60 hover:bg-white/10",
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex flex-col space-y-1">
          <span className="text-2xl">{emoji}</span>
          <p className="text-lg font-semibold text-white">{title}</p>
          <p className="text-sm text-slate-300/80">{subtitle}</p>
        </div>
        <div
          className={cn(
            "rounded-full border px-3 py-1 text-xs font-medium",
            active ? "border-emerald-400/70 bg-emerald-400/10 text-emerald-100" : "border-white/10 text-slate-300",
          )}
        >
          {active ? "已选择" : "选择"}
        </div>
      </div>
      <div className="mt-4 flex items-center justify-between text-xs text-slate-300/80">
        <span>适合此类拍摄方案</span>
        <span className="text-emerald-200/90 group-hover:text-emerald-100">点击继续 →</span>
      </div>
    </button>
  );
}
