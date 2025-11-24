import type { DetailedHTMLProps, InputHTMLAttributes } from "react";
import { cn } from "../../utils/cn";

export type InputProps = DetailedHTMLProps<
  InputHTMLAttributes<HTMLInputElement>,
  HTMLInputElement
>;

export function Input({ className, ...props }: InputProps) {
  return (
    <input
      className={cn(
        "h-11 w-full rounded-xl border border-white/10 bg-white/5 px-4 text-sm text-white outline-none transition focus:border-emerald-400/60 focus-visible:ring-2 focus-visible:ring-emerald-400/30 placeholder:text-slate-500 disabled:cursor-not-allowed disabled:opacity-60",
        className,
      )}
      {...props}
    />
  );
}
