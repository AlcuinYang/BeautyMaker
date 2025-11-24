import { motion } from "framer-motion";
import type { MouseEvent } from "react";

interface ImagePreviewModalProps {
  src: string | null;
  onClose: () => void;
}

export function ImagePreviewModal({ src, onClose }: ImagePreviewModalProps) {
  if (!src) {
    return null;
  }

  const handleBackgroundClick = (event: MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
      onClick={handleBackgroundClick}
      role="button"
      tabIndex={-1}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        className="relative max-h-[90vh] max-w-[90vw] overflow-hidden rounded-2xl border border-white/10 bg-black/20 p-3"
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 rounded-full border border-white/10 bg-black/60 px-3 py-1 text-xs text-slate-200 hover:border-emerald-400/60 hover:text-white"
        >
          关闭
        </button>
        <img src={src} alt="预览大图" className="max-h-[80vh] max-w-[80vw] rounded-xl object-contain" />
      </motion.div>
    </div>
  );
}
