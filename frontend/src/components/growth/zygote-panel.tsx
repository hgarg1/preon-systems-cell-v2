"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  birthZygote,
  createZygote,
  developZygote,
  feedOrganism,
  getOrganismHealth,
  grantOxygen,
  negotiateReproduction,
} from "@/lib/api";
import type { OrganismRecord, ZygoteRecord } from "@/lib/api";

export function ZygotePanel({
  organisms,
  onRefresh,
}: {
  organisms: OrganismRecord[];
  onRefresh: () => Promise<void>;
}) {
  const [motherIndex, setMotherIndex] = useState(0);
  const [fatherIndex, setFatherIndex] = useState(organisms.length > 1 ? 1 : 0);
  const [zygote, setZygote] = useState<ZygoteRecord | null>(null);
  const [negotiation, setNegotiation] = useState<Record<string, unknown> | null>(null);
  const [healthData, setHealthData] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [output, setOutput] = useState<unknown>(null);

  const mother = organisms[motherIndex];
  const father = organisms[fatherIndex] ?? organisms[0];

  async function run(action: string) {
    if (!mother || !father) return;
    setBusy(action);
    try {
      if (action === "negotiate") {
        const neg = await negotiateReproduction({ motherOrganismId: mother.organism_id, fatherOrganismId: father.organism_id });
        setNegotiation(neg);
        setOutput({ negotiation: neg });
      } else if (action === "create") {
        const z = await createZygote({ motherOrganismId: mother.organism_id, fatherOrganismId: father.organism_id });
        setZygote(z);
        setOutput({ zygote: z });
      } else if (action === "develop") {
        if (!zygote) return;
        const z = await developZygote(zygote.zygote_id, "embryo");
        setZygote(z);
        setOutput({ zygote: z });
      } else if (action === "birth") {
        if (!zygote) return;
        const born = await birthZygote(zygote.zygote_id);
        setOutput({ born });
        setZygote(null);
        await onRefresh();
      } else if (action === "food") {
        const food = await feedOrganism(mother.organism_id);
        setOutput({ food });
      } else if (action === "oxygen") {
        const oxygen = await grantOxygen(mother.organism_id);
        setOutput({ oxygen });
      } else if (action === "health") {
        const health = await getOrganismHealth(mother.organism_id);
        setHealthData(health);
        setOutput({ health });
      }
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
      {/* Controls */}
      <div className="space-y-5">
        {/* Parent selection */}
        <div className="rounded-lg border border-white/10 bg-neutral-900 p-4">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-neutral-500">Parents</h3>
          {organisms.length < 2 ? (
            <p className="text-sm text-neutral-600">Need at least 2 organisms for reproduction.</p>
          ) : (
            <div className="space-y-3">
              <div>
                <p className="mb-1 text-xs text-neutral-500">Mother (env + data)</p>
                <div className="space-y-1">
                  {organisms.map((o, i) => (
                    <button
                      key={o.organism_id}
                      onClick={() => setMotherIndex(i)}
                      className={`w-full rounded-md px-3 py-2 text-left text-sm transition-colors ${
                        motherIndex === i
                          ? "bg-emerald-400/10 text-emerald-300 border border-emerald-400/30"
                          : "border border-white/10 text-neutral-400 hover:border-white/20"
                      }`}
                    >
                      {o.identity_profile.name}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <p className="mb-1 text-xs text-neutral-500">Father (strategy + blueprint)</p>
                <div className="space-y-1">
                  {organisms.map((o, i) => (
                    <button
                      key={o.organism_id}
                      onClick={() => setFatherIndex(i)}
                      className={`w-full rounded-md px-3 py-2 text-left text-sm transition-colors ${
                        fatherIndex === i
                          ? "bg-violet-400/10 text-violet-300 border border-violet-400/30"
                          : "border border-white/10 text-neutral-400 hover:border-white/20"
                      }`}
                    >
                      {o.identity_profile.name}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Zygote lifecycle */}
        <div className="rounded-lg border border-white/10 bg-neutral-900 p-4">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-neutral-500">Reproduction</h3>
          <div className="space-y-2">
            {[
              ["negotiate", "Negotiate Gametes"],
              ["create",    "Create Zygote"],
              ["develop",   "Develop → Embryo"],
              ["birth",     "Birth Organism"],
            ].map(([action, label]) => (
              <Button
                key={action}
                size="sm"
                variant="outline"
                className="w-full justify-start border-white/10 text-neutral-300"
                disabled={busy !== null || (action === "develop" || action === "birth" ? !zygote : false)}
                onClick={() => run(action)}
              >
                {busy === action ? "Working…" : label}
              </Button>
            ))}
          </div>
          {zygote ? (
            <div className="mt-3 rounded-md border border-white/10 p-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-neutral-400">Zygote stage</span>
                <Badge variant="outline" className="text-[10px] border-violet-400/30 text-violet-300">
                  {zygote.stage}
                </Badge>
              </div>
              <p className="mt-1 font-mono text-[10px] text-neutral-600">{zygote.zygote_id}</p>
            </div>
          ) : null}
        </div>

        {/* Life support */}
        <div className="rounded-lg border border-white/10 bg-neutral-900 p-4">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-neutral-500">Life Support (Mother)</h3>
          <div className="space-y-2">
            {[
              ["food",   "Feed Information"],
              ["oxygen", "Grant Oxygen"],
              ["health", "Load Health"],
            ].map(([action, label]) => (
              <Button
                key={action}
                size="sm"
                variant="outline"
                className="w-full justify-start border-white/10 text-neutral-300"
                disabled={busy !== null}
                onClick={() => run(action)}
              >
                {busy === action ? "Working…" : label}
              </Button>
            ))}
          </div>
          {healthData ? (
            <div className="mt-3 grid grid-cols-2 gap-1 text-xs text-neutral-500">
              {Object.entries(healthData).slice(0, 6).map(([k, v]) => (
                <span key={k}>{k}: {String(v)}</span>
              ))}
            </div>
          ) : null}
        </div>
      </div>

      {/* Output */}
      <div className="rounded-lg border border-white/10 bg-neutral-900/50 p-5">
        <h3 className="mb-3 text-sm font-medium text-neutral-400">Output</h3>
        {output ? (
          <pre className="max-h-[600px] overflow-auto text-xs text-neutral-300">
            {JSON.stringify(output, null, 2)}
          </pre>
        ) : (
          <p className="text-sm text-neutral-600">Run a reproduction or life support action to see output</p>
        )}
      </div>
    </div>
  );
}
