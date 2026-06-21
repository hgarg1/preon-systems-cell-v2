"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { blockStructureRequest, resolveStructureRequest } from "@/lib/api";
import type { StructureRequest } from "@/lib/api";

export function StructureQueue({
  requests,
  onRefresh,
}: {
  requests: StructureRequest[];
  onRefresh: () => Promise<void>;
}) {
  const [busy, setBusy] = useState<string | null>(null);

  async function handleResolve(id: string) {
    setBusy(`resolve-${id}`);
    try { await resolveStructureRequest(id); await onRefresh(); } finally { setBusy(null); }
  }

  async function handleBlock(id: string) {
    setBusy(`block-${id}`);
    try { await blockStructureRequest(id, "Blocked by operator"); await onRefresh(); } finally { setBusy(null); }
  }

  if (!requests.length) {
    return (
      <div className="rounded-lg border border-dashed border-white/10 py-10 text-center">
        <p className="text-sm text-neutral-600">No pending structure requests</p>
        <p className="mt-1 text-xs text-neutral-700">Cells emit these when they lack a contract to complete a signal</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {requests.map((req) => (
        <div key={req.request_id} className="rounded-lg border border-white/10 bg-neutral-900/80 p-4">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <code className="text-sm font-medium text-pink-300">{req.requested_contract}</code>
            <Badge
              variant="outline"
              className={`text-xs ${
                req.status === "open"
                  ? "border-amber-400/40 text-amber-300"
                  : req.status === "resolved"
                  ? "border-green-400/40 text-green-300"
                  : "border-red-400/40 text-red-300"
              }`}
            >
              {req.status}
            </Badge>
          </div>
          <p className="mt-2 text-sm text-neutral-400">{req.reason}</p>
          <div className="mt-2 flex flex-wrap gap-3 text-xs text-neutral-600">
            <span>org: {req.organism_id.slice(0, 8)}…</span>
            <span>{new Date(req.created_at).toLocaleString()}</span>
          </div>
          {req.status === "open" ? (
            <div className="mt-3 flex gap-2">
              <Button
                size="sm"
                variant="outline"
                className="border-emerald-400/30 text-emerald-300 hover:bg-emerald-400/10"
                disabled={busy !== null}
                onClick={() => handleResolve(req.request_id)}
              >
                {busy === `resolve-${req.request_id}` ? "Resolving…" : "Resolve"}
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="border-red-400/30 text-red-300 hover:bg-red-400/10"
                disabled={busy !== null}
                onClick={() => handleBlock(req.request_id)}
              >
                {busy === `block-${req.request_id}` ? "Blocking…" : "Block"}
              </Button>
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}
