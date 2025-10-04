import { ReactNode } from "react";

type CardProps = {
  children: ReactNode;
  className?: string;
};

export function Card({ children, className }: CardProps) {
  return (
    <div
      className={`rounded-2xl border border-white/5 bg-slate-950/70 p-6 shadow-lg${
        className ? ` ${className}` : ""
      }`}
    >
      {children}
    </div>
  );
}
