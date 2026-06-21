"use client";

import { Badge } from "@/components/ui/badge";
import type { CellRecord } from "@/lib/api";

function healthBadge(health: CellRecord["health_state"]): string {
  switch (health) {
    case "alive":    return "border-green-400/40 bg-green-400/10 text-green-300";
    case "stressed": return "border-amber-400/40 bg-amber-400/10 text-amber-300";
    case "degraded": return "border-orange-400/40 bg-orange-400/10 text-orange-300";
    case "hibernating": return "border-yellow-400/40 bg-yellow-400/10 text-yellow-300";
    case "self_consuming": return "border-red-400/40 bg-red-400/10 text-red-200";
    case "dead":     return "border-neutral-600 bg-neutral-800 text-neutral-500";
    default:         return "border-white/20 text-neutral-400";
  }
}

function HealthBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = score > 0.7 ? "bg-green-500" : score > 0.4 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-20 flex-shrink-0 rounded-full bg-white/10">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-neutral-500">{pct}%</span>
    </div>
  );
}

export function CellTable({ cells }: { cells: CellRecord[] }) {
  if (!cells.length) {
    return (
      <div className="rounded-lg border border-dashed border-white/10 py-16 text-center">
        <p className="text-sm text-neutral-600">No cells assigned to this organism</p>
      </div>
    );
  }

  return (
    <div className="grid gap-3">
      {cells.map((cell) => (
        <div key={cell.cell_id} className="rounded-lg border border-white/10 bg-neutral-900/80 p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <code className="text-sm font-medium text-white">{cell.cell_id.slice(0, 16)}…</code>
                <Badge variant="outline" className="text-[10px] border-white/15 text-neutral-400">
                  {cell.cell_type}
                </Badge>
              </div>
              <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-neutral-500">
                <span>tissue: {cell.tissue_id}</span>
                {cell.organ_id ? <span>organ: {cell.organ_id}</span> : null}
                <span>gen {cell.generation}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className={`text-xs ${healthBadge(cell.health_state)}`}>
                {cell.health_state}
              </Badge>
              <Badge variant="outline" className="text-xs border-white/15 text-neutral-400">
                {cell.lifecycle_state}
              </Badge>
            </div>
          </div>

          <div className="mt-3 flex flex-wrap gap-6">
            <div>
              <p className="mb-1 text-[10px] text-neutral-600">Health</p>
              <HealthBar score={cell.health_score} />
            </div>
            <div>
              <p className="mb-1 text-[10px] text-neutral-600">Resources</p>
              <div className="flex gap-3 text-xs text-neutral-400">
                <span>cpu: {cell.resource_budget.compute_units ?? 0}</span>
                <span>mem: {cell.resource_budget.memory_units ?? 0}</span>
                <span>tools: {cell.resource_budget.tool_calls ?? 0}</span>
              </div>
            </div>
            {Object.keys(cell.expression_profile).length ? (
              <div>
                <p className="mb-1 text-[10px] text-neutral-600">Expression Profile</p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(cell.expression_profile).map(([k, v]) => (
                    <span key={k} className="text-xs text-neutral-400">
                      {k}: {v.toFixed(2)}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      ))}
    </div>
  );
}
