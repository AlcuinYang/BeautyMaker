import type { ReactNode } from "react";

interface BadgeProps {
  children: ReactNode;
  variant?: "free" | "paid" | "active" | "default";
}

const variantStyles: Record<Required<BadgeProps>["variant"], string> = {
  free: "bg-emerald-500/20 text-emerald-200 border border-emerald-400/40",
  paid: "bg-purple-500/20 text-purple-200 border border-purple-400/40",
  active: "bg-sky-500/20 text-sky-200 border border-sky-400/40",
  default: "bg-white/10 text-slate-200 border border-white/20",
};

export function Badge({ children, variant = "default" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${
        variantStyles[variant]
      }`}
    >
      {children}
    </span>
  );
}
