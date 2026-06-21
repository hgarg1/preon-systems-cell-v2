"use client";

import { Badge } from "@/components/ui/badge";
import type { GenomeModule } from "@/lib/api";

const STRATEGY_COLORS: Record<string, string> = {
  precomputed:       "border-blue-400/40 bg-blue-400/10 text-blue-300",
  deterministic_tool:"border-emerald-400/40 bg-emerald-400/10 text-emerald-300",
  llm_stub:          "border-violet-400/40 bg-violet-400/10 text-violet-300",
};

export function ModuleCard({ module: m }: { module: GenomeModule }) {
  return (
    <div className="rounded-lg border border-white/10 bg-neutral-900/80 p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-mono text-sm font-medium text-white">{m.module_id}</p>
          <div className="mt-1.5 flex flex-wrap gap-1">
            {m.signal_types.map((t) => (
              <Badge key={t} variant="outline" className="text-[10px] border-white/15 text-neutral-400">
                {t}
              </Badge>
            ))}
          </div>
        </div>
        <Badge
          variant="outline"
          className={`flex-shrink-0 text-[10px] ${STRATEGY_COLORS[m.execution_strategy] ?? "border-white/20 text-neutral-400"}`}
        >
          {m.execution_strategy}
        </Badge>
      </div>
      {m.deterministic_tool ? (
        <p className="mt-2 text-xs text-neutral-500">
          tool: <span className="font-mono text-neutral-300">{m.deterministic_tool}</span>
        </p>
      ) : null}
    </div>
  );
}
