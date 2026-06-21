"use client";

import { ModuleCard } from "./module-card";
import type { Genome } from "@/lib/api";

export function GenomeViewer({ genome }: { genome: Genome }) {
  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_1.5fr]">
      {/* Left: Core instruction set + regulatory rules */}
      <div className="space-y-6">
        <section>
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-neutral-500">
            Core Instruction Set
          </h3>
          <div className="rounded-lg border border-white/10 bg-neutral-900/80 divide-y divide-white/5">
            {genome.core_instruction_set.length ? (
              genome.core_instruction_set.map((instruction, i) => (
                <div key={i} className="flex items-center gap-2 px-4 py-2.5">
                  <span className="size-1.5 flex-shrink-0 rounded-full bg-emerald-500" />
                  <code className="text-sm text-neutral-200">{instruction}</code>
                </div>
              ))
            ) : (
              <p className="px-4 py-3 text-sm text-neutral-600">No instructions defined</p>
            )}
          </div>
        </section>

        <section>
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-neutral-500">
            Regulatory Rules
          </h3>
          {genome.regulatory_rules.length ? (
            <div className="space-y-2">
              {genome.regulatory_rules.map((rule, i) => (
                <div key={i} className="rounded-md border border-white/10 bg-neutral-900/80 p-3">
                  <pre className="text-xs text-neutral-300 whitespace-pre-wrap">
                    {JSON.stringify(rule, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-md border border-white/10 bg-neutral-900/80 px-4 py-3 text-sm text-neutral-600">
              No regulatory rules
            </div>
          )}
        </section>

        <section>
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-neutral-500">
            Constraints
          </h3>
          <div className="rounded-md border border-white/10 bg-neutral-900/80 p-3">
            <pre className="text-xs text-neutral-300">
              {JSON.stringify(genome.constraints, null, 2)}
            </pre>
          </div>
        </section>
      </div>

      {/* Right: Modules */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-500">
            Modules
          </h3>
          <span className="text-xs text-neutral-600">v{genome.version}</span>
        </div>
        {genome.modules.length ? (
          <div className="space-y-3">
            {genome.modules.map((m) => (
              <ModuleCard key={m.module_id} module={m} />
            ))}
          </div>
        ) : (
          <div className="rounded-lg border border-dashed border-white/10 py-12 text-center">
            <p className="text-sm text-neutral-600">No modules in genome</p>
          </div>
        )}
      </div>
    </div>
  );
}
