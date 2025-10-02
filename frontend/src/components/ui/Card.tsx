import { ReactNode } from "react";

export function Card({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-2xl border border-white/5 bg-slate-950/70 p-6 shadow-lg">
      {children}
    </div>
  );
}
