"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { deprecateMemory, type MemoryRecord } from "@/lib/api";

function statusBadge(s: MemoryRecord["status"]): string {
  switch (s) {
    case "active":   return "border-green-400/40 text-green-300";
    case "approved": return "border-emerald-400/40 text-emerald-300";
    case "pending":  return "border-amber-400/40 text-amber-300";
    case "rejected": return "border-red-400/40 text-red-300";
    case "deprecated": return "border-neutral-600 text-neutral-500";
    case "expired": return "border-orange-500/40 text-orange-300";
    case "superseded": return "border-blue-500/40 text-blue-300";
    default:         return "border-white/20 text-neutral-400";
  }
}

export function MemoryTable({
  organismId,
  records,
  onChanged,
}: {
  organismId: string;
  records: MemoryRecord[];
  onChanged: () => Promise<void>;
}) {
  const [busyId, setBusyId] = useState<string | null>(null);

  async function deprecate(memoryId: string) {
    setBusyId(memoryId);
    try {
      await deprecateMemory(organismId, memoryId);
      await onChanged();
    } finally {
      setBusyId(null);
    }
  }

  if (!records.length) {
    return (
      <div className="rounded-lg border border-dashed border-white/10 py-16 text-center">
        <p className="text-sm text-neutral-600">No memory records for this organism</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {records.map((rec) => (
        <div key={rec.memory_id} className="rounded-lg border border-white/10 bg-neutral-900/80 p-4">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline" className="text-xs border-white/15 text-neutral-300">{rec.scope}</Badge>
              <Badge variant="outline" className="text-xs border-white/15 text-neutral-400">{rec.kind}</Badge>
              <Badge variant="outline" className="text-xs border-cyan-400/30 text-cyan-300">{rec.memory_type}</Badge>
              <Badge variant="outline" className="text-xs border-white/15 text-neutral-400">{rec.data_class}</Badge>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className={`text-xs ${statusBadge(rec.status)}`}>{rec.status}</Badge>
              <span className="text-xs text-neutral-600">v{rec.version}</span>
              <span className="text-xs text-neutral-600">conf: {rec.confidence.toFixed(2)}</span>
              <span className="text-xs text-neutral-600">importance: {rec.importance.toFixed(2)}</span>
            </div>
          </div>
          <pre className="mt-3 max-h-32 overflow-auto rounded-md bg-neutral-950 p-2 text-xs text-neutral-300">
            {JSON.stringify(rec.payload, null, 2)}
          </pre>
          <p className="mt-2 text-xs text-neutral-600">{new Date(rec.created_at).toLocaleString()}</p>
          <div className="mt-2 grid gap-1 text-xs text-neutral-500 sm:grid-cols-2">
            <span>Admission: {rec.promotion_reason}</span>
            <span>Accesses: {rec.access_count}{rec.last_accessed_at ? ` · last ${new Date(rec.last_accessed_at).toLocaleString()}` : ""}</span>
            <span>Signal: {rec.source_signal_id ?? "operator"}</span>
            <span>Run: {rec.source_run_id ?? "—"}</span>
            <span className="truncate">Proteins: {rec.source_protein_ids.join(", ") || "—"}</span>
            <span>TTL: {rec.ttl_seconds === null ? "none" : `${rec.ttl_seconds}s`}</span>
          </div>
          {rec.status === "active" ? (
            <Button
              size="sm"
              variant="outline"
              className="mt-3"
              disabled={busyId === rec.memory_id}
              onClick={() => void deprecate(rec.memory_id)}
            >
              {busyId === rec.memory_id ? "Deprecating…" : "Deprecate"}
            </Button>
          ) : null}
        </div>
      ))}
    </div>
  );
}
