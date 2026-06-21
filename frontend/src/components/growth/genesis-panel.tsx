"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Atom } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createOrganism } from "@/lib/api";

export function GenesisPanel({ onCreated }: { onCreated: () => Promise<void> }) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [purpose, setPurpose] = useState("");
  const [goalInput, setGoalInput] = useState("");
  const [goals, setGoals] = useState<string[]>([
    "Survive on available food and oxygen",
    "Form memory from every signal processed",
    "Develop capability over time",
  ]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function addGoal() {
    const g = goalInput.trim();
    if (!g || goals.includes(g)) return;
    setGoals(prev => [...prev, g]);
    setGoalInput("");
  }

  function removeGoal(g: string) {
    setGoals(prev => prev.filter(x => x !== g));
  }

  async function handleCreate() {
    if (!name.trim() || goals.length === 0) return;
    setBusy(true);
    setError(null);
    try {
      const organism = await createOrganism({
        name: name.trim(),
        purpose: purpose.trim() || "First organism — bootstrapped without parents",
        goals,
      });
      await onCreated();
      router.push(`/organisms/${organism.organism_id}/console`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create organism");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl">
      <div className="mb-6 flex items-center gap-3">
        <div className="flex size-10 items-center justify-center rounded-full border border-emerald-400/30 bg-emerald-400/10">
          <Atom className="size-5 text-emerald-400" />
        </div>
        <div>
          <h3 className="font-semibold text-white">Spark Genesis</h3>
          <p className="text-xs text-neutral-500">No parents. No lineage. The first organism is born from intent alone.</p>
        </div>
      </div>

      <div className="rounded-lg border border-white/10 bg-neutral-900 p-5 space-y-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <Label htmlFor="gen-name" className="text-xs text-neutral-400">Name</Label>
            <Input
              id="gen-name"
              placeholder="Adam"
              value={name}
              onChange={e => setName(e.target.value)}
              className="mt-1.5 border-white/10 bg-neutral-800 text-neutral-200 placeholder-neutral-600"
            />
          </div>
          <div>
            <Label htmlFor="gen-purpose" className="text-xs text-neutral-400">Purpose</Label>
            <Input
              id="gen-purpose"
              placeholder="What this organism exists to do"
              value={purpose}
              onChange={e => setPurpose(e.target.value)}
              className="mt-1.5 border-white/10 bg-neutral-800 text-neutral-200 placeholder-neutral-600"
            />
          </div>
        </div>

        <div>
          <Label className="text-xs text-neutral-400">Goals</Label>
          <div className="mt-1.5 flex gap-2">
            <Input
              placeholder="Add a goal…"
              value={goalInput}
              onChange={e => setGoalInput(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter") { e.preventDefault(); addGoal(); } }}
              className="border-white/10 bg-neutral-800 text-neutral-200 placeholder-neutral-600"
            />
            <Button
              size="sm"
              variant="outline"
              className="shrink-0 border-white/10 text-neutral-300"
              onClick={addGoal}
              disabled={!goalInput.trim()}
            >
              Add
            </Button>
          </div>
          {goals.length > 0 && (
            <ul className="mt-2 space-y-1">
              {goals.map(g => (
                <li key={g} className="flex items-center justify-between rounded-md border border-white/10 px-3 py-1.5 text-xs text-neutral-300">
                  <span>{g}</span>
                  <button onClick={() => removeGoal(g)} className="ml-3 text-neutral-600 hover:text-neutral-400">×</button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {error && (
          <div className="rounded-md border border-red-400/30 bg-red-400/10 px-3 py-2 text-xs text-red-300">{error}</div>
        )}

        <Button
          onClick={handleCreate}
          disabled={busy || !name.trim() || goals.length === 0}
          className="w-full bg-emerald-500 text-white hover:bg-emerald-400 disabled:opacity-40"
        >
          {busy ? "Sparking…" : "Spark Genesis"}
        </Button>
      </div>

      <p className="mt-4 text-center text-[11px] text-neutral-700">
        After creation, provision food and oxygen in the Primordial Soup tab to begin metabolism.
      </p>
    </div>
  );
}
