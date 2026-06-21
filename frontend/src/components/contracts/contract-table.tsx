"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { deprecateContract } from "@/lib/api";
import type { Contract } from "@/lib/api";

export function ContractTable({ contracts, onRefresh }: { contracts: Contract[]; onRefresh: () => Promise<void> }) {
  const [busy, setBusy] = useState<string | null>(null);

  async function handleDeprecate(id: string) {
    setBusy(id);
    try { await deprecateContract(id); await onRefresh(); } finally { setBusy(null); }
  }

  if (!contracts.length) {
    return (
      <div className="rounded-lg border border-dashed border-white/10 py-12 text-center">
        <p className="text-sm text-neutral-600">No contracts registered</p>
      </div>
    );
  }

  return (
    <div className="grid gap-3 md:grid-cols-2">
      {contracts.map((c) => (
        <div key={c.contract_id} className="rounded-lg border border-white/10 bg-neutral-900/80 p-4">
          <div className="flex items-start justify-between gap-2">
            <code className="text-sm font-medium text-white break-all">{c.name}</code>
            <Badge
              variant="outline"
              className={`flex-shrink-0 text-xs ${
                c.status === "active"
                  ? "border-green-400/40 text-green-300"
                  : "border-neutral-600 text-neutral-500"
              }`}
            >
              {c.status}
            </Badge>
          </div>

          <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-neutral-500">
            <span>usage: {c.usage_count}</span>
            <span>actions: {c.allowed_actions.join(", ") || "any"}</span>
            <span>permissions: {c.permissions.join(", ") || "none"}</span>
            <span>deps: {c.dependencies.join(", ") || "none"}</span>
            {c.deprecated_reason ? (
              <span className="col-span-2 text-amber-400">deprecated: {c.deprecated_reason}</span>
            ) : null}
          </div>

          <details className="mt-3">
            <summary className="cursor-pointer text-[10px] text-neutral-600 hover:text-neutral-400">schema</summary>
            <pre className="mt-1 max-h-24 overflow-auto rounded bg-neutral-950 p-2 text-[10px] text-neutral-400">
              {JSON.stringify(c.schema, null, 2)}
            </pre>
          </details>

          <div className="mt-3">
            <Button
              size="sm"
              variant="outline"
              className="border-white/10 text-xs text-neutral-400 hover:text-white"
              disabled={c.status === "deprecated" || busy === c.contract_id}
              onClick={() => handleDeprecate(c.contract_id)}
            >
              {busy === c.contract_id ? "Deprecating…" : "Deprecate"}
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}
