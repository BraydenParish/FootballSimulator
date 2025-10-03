import { type HTMLAttributes, type ReactNode } from "react";

type CardProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  className?: string;
};

export function Card({ children, className, ...rest }: CardProps) {
  return (
    <div
      {...rest}
      className={`rounded-2xl border border-white/5 bg-slate-950/70 p-6 shadow-lg${
        className ? ` ${className}` : ""
      }`}
    >
      {children}
    </div>
  );
}
