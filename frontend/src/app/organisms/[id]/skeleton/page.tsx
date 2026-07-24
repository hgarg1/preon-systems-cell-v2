"use client";

import { use, useCallback, useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  approveStructureProposal,
  getSkeleton,
  reconcileSkeleton,
  rejectStructureProposal,
  revokeSkeletonGrant,
  type SkeletonDetail,
} from "@/lib/api";

export default function SkeletonPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [detail, setDetail] = useState<SkeletonDetail | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setDetail(await getSkeleton(id));
  }, [id]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const activeEffects = detail?.effects.some(
    (effect) => effect.status === "pending" || effect.status === "processing",
  );
  useEffect(() => {
    if (!activeEffects) return;
    const interval = window.setInterval(() => void refresh(), 1000);
    return () => window.clearInterval(interval);
  }, [activeEffects, refresh]);

  async function act(key: string, operation: () => Promise<unknown>) {
    setBusy(key);
    try {
      await operation();
      await refresh();
    } finally {
      setBusy(null);
    }
  }

  if (!detail) return <div className="p-6 text-sm text-neutral-500">Loading skeleton…</div>;

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-white">Living skeleton</h2>
          <p className="mt-1 text-sm text-neutral-400">
            Cellular provenance, governed resources, scoped grants, and provider reconciliation.
          </p>
        </div>
        <Button
          size="sm"
          variant="outline"
          disabled={busy !== null}
          onClick={() => void act("reconcile", () => reconcileSkeleton(id))}
        >
          {busy === "reconcile" ? "Reconciling…" : "Reconcile"}
        </Button>
      </div>

      <section>
        <h3 className="mb-3 text-sm font-medium text-neutral-300">Skeletal cells</h3>
        <div className="grid gap-3 md:grid-cols-3">
          {detail.cells.map((cell) => (
            <div key={cell.cell_id} className="rounded-lg border border-white/10 bg-neutral-900/80 p-4">
              <div className="flex items-center justify-between">
                <span className="font-medium text-white">{cell.cell_type}</span>
                <Badge variant="outline">{cell.lifecycle_state}</Badge>
              </div>
              <p className="mt-2 break-all text-xs text-neutral-500">{cell.cell_id}</p>
              <p className="mt-1 text-xs text-neutral-500">genome: {cell.cell_genome_id}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h3 className="mb-3 text-sm font-medium text-neutral-300">Structural resources</h3>
        <div className="space-y-3">
          {detail.resources.length === 0 ? (
            <p className="rounded-lg border border-dashed border-white/10 p-5 text-sm text-neutral-600">No resources grown yet.</p>
          ) : detail.resources.map((resource) => (
            <div key={resource.bone_id} className="rounded-lg border border-white/10 bg-neutral-900/80 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium text-white">{resource.name}</span>
                <Badge variant="outline">{resource.structure_type}</Badge>
                <Badge variant="outline">{resource.provider}</Badge>
                <Badge variant="outline">{resource.health}</Badge>
                <span className="ml-auto text-xs text-neutral-500">generation {resource.generation}</span>
              </div>
              <p className="mt-2 break-all text-xs text-neutral-500">{resource.provider_resource_ref ?? "not materialized"}</p>
              <pre className="mt-3 overflow-x-auto rounded bg-black/30 p-3 text-xs text-neutral-400">
                {JSON.stringify({ desired: resource.definition, observed: resource.observed_state }, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h3 className="mb-3 text-sm font-medium text-neutral-300">Proposals and effects</h3>
        <div className="space-y-3">
          {detail.proposals.map((proposal) => {
            const effect = detail.effects.find((item) => item.proposal_id === proposal.proposal_id);
            return (
              <div key={proposal.proposal_id} className="rounded-lg border border-white/10 bg-neutral-900/80 p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium text-white">{proposal.name}</span>
                  <Badge variant="outline">{proposal.operation}</Badge>
                  <Badge variant="outline">{proposal.status}</Badge>
                  <Badge variant="outline">{proposal.apply_status}</Badge>
                </div>
                <p className="mt-2 break-all font-mono text-[11px] text-neutral-600">digest {proposal.plan_digest}</p>
                {effect ? (
                  <p className="mt-1 text-xs text-neutral-500">
                    effect {effect.status} · attempt {effect.attempt_count}/{effect.max_attempts}
                    {effect.last_error ? ` · ${effect.last_error}` : ""}
                  </p>
                ) : null}
                {proposal.status === "pending" ? (
                  <div className="mt-3 flex gap-2">
                    <Button
                      size="sm"
                      disabled={busy !== null}
                      onClick={() => void act(proposal.proposal_id, () => approveStructureProposal(proposal.proposal_id, proposal.plan_digest))}
                    >
                      Approve exact plan
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={busy !== null}
                      onClick={() => void act(proposal.proposal_id, () => rejectStructureProposal(proposal.proposal_id))}
                    >
                      Reject
                    </Button>
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      </section>

      <section>
        <h3 className="mb-3 text-sm font-medium text-neutral-300">Scoped grants</h3>
        <div className="space-y-2">
          {detail.grants.map((grant) => (
            <div key={grant.grant_id} className="flex flex-wrap items-center gap-2 rounded-lg border border-white/10 p-3 text-sm">
              <span className="text-white">{grant.permissions.join(", ")}</span>
              <span className="text-neutral-500">cell {grant.cell_id}</span>
              <Badge variant="outline">{grant.status}</Badge>
              {grant.status === "active" ? (
                <Button
                  size="sm"
                  variant="outline"
                  className="ml-auto"
                  disabled={busy !== null}
                  onClick={() => void act(grant.grant_id, () => revokeSkeletonGrant(id, grant.grant_id))}
                >
                  Revoke
                </Button>
              ) : null}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
