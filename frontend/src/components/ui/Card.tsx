import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "../../utils/cn";

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export function Card({ className, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-3xl border border-white/10 bg-white/5 p-6 text-sm text-slate-200 backdrop-blur-xl",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
