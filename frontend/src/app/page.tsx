"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Moon, Plus, Terminal, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useOrganisms } from "@/lib/organisms-context";
import { createOrganism, hibernateOrganism, wakeOrganism } from "@/lib/api";
import type { LifecycleState } from "@/lib/api";

function lifecycleBadge(state: LifecycleState): string {
  switch (state) {
    case "active":     return "border-green-400/40 bg-green-400/10 text-green-300";
    case "hibernated": return "border-yellow-400/40 bg-yellow-400/10 text-yellow-300";
    case "degraded":   return "border-orange-400/40 bg-orange-400/10 text-orange-300";
    case "terminated": return "border-red-400/40 bg-red-400/10 text-red-300";
    default:           return "border-white/20 text-neutral-400";
  }
}

export default function OrganismListPage() {
  const { organisms, loading, refresh } = useOrganisms();
  const router = useRouter();
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [newPurpose, setNewPurpose] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate() {
    if (!newName.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const created = await createOrganism({
        name: newName.trim(),
        purpose: newPurpose.trim() || "Deterministic cell survival runtime",
        goals: ["Process admitted signals", "Preserve identity across hibernation"],
      });
      await refresh();
      setShowForm(false);
      setNewName("");
      setNewPurpose("");
      router.push(`/organisms/${created.organism_id}/console`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create organism");
    } finally {
      setCreating(false);
    }
  }

  async function handleWake(id: string) {
    setBusy(`wake-${id}`);
    setError(null);
    try { await wakeOrganism(id); await refresh(); } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally { setBusy(null); }
  }

  async function handleHibernate(id: string) {
    setBusy(`hibernate-${id}`);
    setError(null);
    try { await hibernateOrganism(id); await refresh(); } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally { setBusy(null); }
  }

  return (
    <div className="px-8 py-8">
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-white">Organisms</h2>
          <p className="mt-1 text-sm text-neutral-400">
            Each organism is a persistent runtime identity with cells, genome, memory, and policies.
          </p>
        </div>
        <Button onClick={() => setShowForm(!showForm)} className="flex-shrink-0">
          <Plus className="mr-2 size-4" />
          New Organism
        </Button>
      </div>

      {error ? (
        <div className="mb-4 rounded-md border border-red-400/30 bg-red-400/10 px-4 py-3 text-sm text-red-300">
          {error}
          {error.toLowerCase().includes("authentication") ? (
            <span className="ml-2">— <a href="/login" className="underline">Sign in</a> or <a href="/signup" className="underline">create an account</a> to continue.</span>
          ) : null}
        </div>
      ) : null}

      {showForm ? (
        <div className="mb-8 rounded-lg border border-white/10 bg-neutral-900 p-5">
          <h3 className="mb-4 text-sm font-medium text-neutral-200">Create Organism</h3>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="org-name">Name</Label>
              <Input
                id="org-name"
                placeholder="Ops Runtime"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="mt-1.5"
              />
            </div>
            <div>
              <Label htmlFor="org-purpose">Purpose</Label>
              <Input
                id="org-purpose"
                placeholder="Answer deterministic work signals"
                value={newPurpose}
                onChange={(e) => setNewPurpose(e.target.value)}
                className="mt-1.5"
              />
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <Button onClick={handleCreate} disabled={creating || !newName.trim()}>
              {creating ? "Creating…" : "Create"}
            </Button>
            <Button variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
          </div>
        </div>
      ) : null}

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-44 rounded-lg border border-white/10 bg-neutral-900 animate-pulse" />
          ))}
        </div>
      ) : organisms.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-white/20 py-20 text-center">
          <p className="text-neutral-500">No organisms yet</p>
          <Button className="mt-4" onClick={() => setShowForm(true)}>
            <Plus className="mr-2 size-4" />
            Create First Organism
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {organisms.map((o) => (
            <div
              key={o.organism_id}
              className="flex flex-col gap-3 rounded-lg border border-white/10 bg-neutral-900 p-5"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <h3 className="truncate font-medium text-white">{o.identity_profile.name}</h3>
                  <p className="mt-0.5 truncate text-xs text-neutral-500">{o.identity_profile.purpose}</p>
                </div>
                <Badge variant="outline" className={`flex-shrink-0 text-xs ${lifecycleBadge(o.lifecycle_state)}`}>
                  {o.lifecycle_state}
                </Badge>
              </div>

              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-neutral-500">
                <span>Stage: {o.development_stage}</span>
                <span>Genome: {o.genome_id.slice(0, 8)}…</span>
                <span>Goals: {o.goals.length}</span>
              </div>

              <div className="mt-auto flex gap-2 pt-1">
                <Link href={`/organisms/${o.organism_id}/console`} className="flex-1">
                  <Button size="sm" variant="outline" className="w-full border-white/15 text-neutral-300 hover:text-white">
                    <Terminal className="mr-1.5 size-3.5" />
                    Console
                  </Button>
                </Link>
                <Button
                  size="sm"
                  variant="outline"
                  className="border-white/15 text-neutral-400 hover:text-white"
                  disabled={busy !== null}
                  onClick={() =>
                    o.lifecycle_state === "active"
                      ? handleHibernate(o.organism_id)
                      : handleWake(o.organism_id)
                  }
                >
                  {o.lifecycle_state === "active" ? (
                    busy === `hibernate-${o.organism_id}` ? "…" : <Moon className="size-3.5" />
                  ) : (
                    busy === `wake-${o.organism_id}` ? "…" : <Zap className="size-3.5" />
                  )}
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
