"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { updateGenomeDivisionPolicy, checkDivisionReadiness } from "@/lib/api";
import type {
  CellRecord,
  DivisionMode,
  DivisionPolicy,
  DivisionReadinessResult,
  Genome,
} from "@/lib/api";

const ALL_MODES: DivisionMode[] = ["symmetric", "asymmetric", "founder", "repair"];

const MODE_DESCRIPTIONS: Record<DivisionMode, string> = {
  symmetric:  "Two identical daughters — pure load distribution",
  asymmetric: "One inherits capability, one begins specializing",
  founder:    "One stays, one becomes a new cell type progenitor",
  repair:     "Replace a dead or degraded cell",
};

const DEFAULT_POLICY: DivisionPolicy = {
  can_divide: true,
  gates: {
    load:       { min_protein_throughput: 10 },
    capability: { min_successful_proteins: 50, min_distinct_signal_types: 3, min_avg_confidence: 0.70 },
    lifecycle:  { max_generation: 10, required_lifecycle_state: "active" },
  },
  allowed_modes: ["symmetric", "asymmetric"],
  preferred_mode: "asymmetric",
  cooldown_ms: 30000,
  max_daughters_per_division: 2,
};

function GateRow({ label, result }: { label: string; result: { passed: boolean; reason: string; measured: Record<string, unknown> } }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`rounded-md border px-3 py-2 text-xs ${result.passed ? "border-emerald-400/20 bg-emerald-400/5" : "border-red-400/20 bg-red-400/5"}`}>
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className={result.passed ? "text-emerald-400" : "text-red-400"}>{result.passed ? "✓" : "✗"}</span>
          <span className="font-medium text-neutral-200">{label}</span>
        </div>
        <button onClick={() => setOpen(o => !o)} className="text-neutral-600 hover:text-neutral-400">
          {open ? "▲" : "▼"}
        </button>
      </div>
      <p className="mt-1 text-neutral-500">{result.reason}</p>
      {open && Object.keys(result.measured).length > 0 && (
        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 border-t border-white/5 pt-2">
          {Object.entries(result.measured).map(([k, v]) => (
            <span key={k} className="text-neutral-600"><span className="text-neutral-500">{k}:</span> {String(v)}</span>
          ))}
        </div>
      )}
    </div>
  );
}

export function DivisionPolicyEditor({
  genome,
  cells,
  onSaved,
}: {
  genome: Genome;
  cells: CellRecord[];
  onSaved: (updated: Genome) => void;
}) {
  const initial = genome.division_policy ?? DEFAULT_POLICY;
  const [policy, setPolicy] = useState<DivisionPolicy>(initial);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [readiness, setReadiness] = useState<DivisionReadinessResult | null>(null);
  const [checking, setChecking] = useState(false);
  const [selectedCellId, setSelectedCellId] = useState(cells[0]?.cell_id ?? "");

  function setGate<K extends keyof DivisionPolicy["gates"]>(
    key: K,
    field: string,
    value: unknown,
  ) {
    setPolicy(p => ({
      ...p,
      gates: { ...p.gates, [key]: { ...p.gates[key], [field]: value } },
    }));
  }

  function toggleMode(mode: DivisionMode) {
    setPolicy(p => {
      const has = p.allowed_modes.includes(mode);
      const next = has ? p.allowed_modes.filter(m => m !== mode) : [...p.allowed_modes, mode];
      return {
        ...p,
        allowed_modes: next,
        preferred_mode: next.includes(p.preferred_mode) ? p.preferred_mode : (next[0] ?? "symmetric"),
      };
    });
  }

  async function save() {
    setSaving(true);
    setError(null);
    try {
      const updated = await updateGenomeDivisionPolicy(genome.genome_id, policy);
      onSaved(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function checkReadiness() {
    if (!selectedCellId) return;
    setChecking(true);
    setReadiness(null);
    try {
      const result = await checkDivisionReadiness(cells.find(c => c.cell_id === selectedCellId)!.organism_id, selectedCellId);
      setReadiness(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Check failed");
    } finally {
      setChecking(false);
    }
  }

  const hasPolicy = genome.division_policy !== null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white">Division Policy</h3>
          <p className="mt-0.5 text-xs text-neutral-500">
            Three gates must all pass before a cell can divide. The genome defines the thresholds.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {hasPolicy ? (
            <Badge variant="outline" className="border-emerald-400/30 text-emerald-300 text-[10px]">Policy active</Badge>
          ) : (
            <Badge variant="outline" className="border-neutral-600 text-neutral-500 text-[10px]">No policy — using defaults</Badge>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left: Policy editor */}
        <div className="space-y-5">
          {/* Master switch */}
          <div className="flex items-center justify-between rounded-lg border border-white/10 bg-neutral-900 px-4 py-3">
            <div>
              <p className="text-sm text-neutral-200">Can divide</p>
              <p className="text-xs text-neutral-600">Globally enable or disable cell division for this genome</p>
            </div>
            <button
              onClick={() => setPolicy(p => ({ ...p, can_divide: !p.can_divide }))}
              className={`relative h-5 w-9 rounded-full transition-colors ${policy.can_divide ? "bg-emerald-500" : "bg-neutral-700"}`}
            >
              <span className={`absolute top-0.5 size-4 rounded-full bg-white transition-all ${policy.can_divide ? "left-4" : "left-0.5"}`} />
            </button>
          </div>

          {/* Load gate */}
          <div className="rounded-lg border border-white/10 bg-neutral-900 p-4 space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-neutral-500">Load Gate</h4>
            <p className="text-[11px] text-neutral-600">Minimum total proteins produced before division adds value. Prevents splitting idle cells.</p>
            <div>
              <Label className="mb-1 text-[10px] uppercase tracking-wider text-neutral-600">Min protein throughput</Label>
              <Input
                type="number"
                min={1}
                value={policy.gates.load.min_protein_throughput}
                onChange={e => setGate("load", "min_protein_throughput", parseInt(e.target.value) || 1)}
                className="h-7 border-white/10 bg-neutral-800 text-xs text-neutral-300"
              />
            </div>
          </div>

          {/* Capability gate */}
          <div className="rounded-lg border border-white/10 bg-neutral-900 p-4 space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-neutral-500">Capability Gate</h4>
            <p className="text-[11px] text-neutral-600">Quality and diversity of outputs. A cell must have demonstrated real capability before seeding daughters.</p>
            <div className="grid grid-cols-3 gap-2">
              <div>
                <Label className="mb-1 text-[10px] uppercase tracking-wider text-neutral-600">Min successful proteins</Label>
                <Input
                  type="number" min={1}
                  value={policy.gates.capability.min_successful_proteins}
                  onChange={e => setGate("capability", "min_successful_proteins", parseInt(e.target.value) || 1)}
                  className="h-7 border-white/10 bg-neutral-800 text-xs text-neutral-300"
                />
              </div>
              <div>
                <Label className="mb-1 text-[10px] uppercase tracking-wider text-neutral-600">Min signal types</Label>
                <Input
                  type="number" min={1}
                  value={policy.gates.capability.min_distinct_signal_types}
                  onChange={e => setGate("capability", "min_distinct_signal_types", parseInt(e.target.value) || 1)}
                  className="h-7 border-white/10 bg-neutral-800 text-xs text-neutral-300"
                />
              </div>
              <div>
                <Label className="mb-1 text-[10px] uppercase tracking-wider text-neutral-600">Min avg confidence</Label>
                <Input
                  type="number" min={0} max={1} step={0.05}
                  value={policy.gates.capability.min_avg_confidence}
                  onChange={e => setGate("capability", "min_avg_confidence", parseFloat(e.target.value) || 0)}
                  className="h-7 border-white/10 bg-neutral-800 text-xs text-neutral-300"
                />
              </div>
            </div>
          </div>

          {/* Lifecycle gate */}
          <div className="rounded-lg border border-white/10 bg-neutral-900 p-4 space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-neutral-500">Lifecycle Gate</h4>
            <p className="text-[11px] text-neutral-600">Generation ceiling and required state. Prevents runaway division and division of stressed cells.</p>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label className="mb-1 text-[10px] uppercase tracking-wider text-neutral-600">Max generation</Label>
                <Input
                  type="number" min={0}
                  value={policy.gates.lifecycle.max_generation}
                  onChange={e => setGate("lifecycle", "max_generation", parseInt(e.target.value) || 0)}
                  className="h-7 border-white/10 bg-neutral-800 text-xs text-neutral-300"
                />
              </div>
              <div>
                <Label className="mb-1 text-[10px] uppercase tracking-wider text-neutral-600">Required state</Label>
                <select
                  value={policy.gates.lifecycle.required_lifecycle_state}
                  onChange={e => setGate("lifecycle", "required_lifecycle_state", e.target.value)}
                  className="h-7 w-full rounded-md border border-white/10 bg-neutral-800 px-2 text-xs text-neutral-300 focus:outline-none"
                >
                  <option value="active">active</option>
                  <option value="hibernated">hibernated</option>
                </select>
              </div>
            </div>
          </div>

          {/* Modes + cooldown */}
          <div className="rounded-lg border border-white/10 bg-neutral-900 p-4 space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-neutral-500">Division Modes</h4>
            <div className="space-y-2">
              {ALL_MODES.map(mode => {
                const allowed = policy.allowed_modes.includes(mode);
                const preferred = policy.preferred_mode === mode;
                return (
                  <div key={mode} className={`flex items-start justify-between gap-2 rounded-md border px-3 py-2 ${allowed ? "border-white/10" : "border-white/5 opacity-50"}`}>
                    <div className="flex items-start gap-2">
                      <input
                        type="checkbox"
                        checked={allowed}
                        onChange={() => toggleMode(mode)}
                        className="mt-0.5 accent-emerald-500"
                      />
                      <div>
                        <p className="text-xs text-neutral-200">{mode}</p>
                        <p className="text-[10px] text-neutral-600">{MODE_DESCRIPTIONS[mode]}</p>
                      </div>
                    </div>
                    {allowed && (
                      <button
                        onClick={() => setPolicy(p => ({ ...p, preferred_mode: mode }))}
                        className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] transition-colors ${preferred ? "bg-emerald-400/10 text-emerald-300" : "text-neutral-600 hover:text-neutral-400"}`}
                      >
                        {preferred ? "preferred" : "set preferred"}
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
            <div>
              <Label className="mb-1 text-[10px] uppercase tracking-wider text-neutral-600">Cooldown after division (ms)</Label>
              <Input
                type="number" min={0} step={1000}
                value={policy.cooldown_ms}
                onChange={e => setPolicy(p => ({ ...p, cooldown_ms: parseInt(e.target.value) || 0 }))}
                className="h-7 border-white/10 bg-neutral-800 text-xs text-neutral-300"
              />
            </div>
          </div>

          {error && (
            <div className="rounded-md border border-red-400/30 bg-red-400/10 px-3 py-2 text-xs text-red-300">{error}</div>
          )}

          <Button
            onClick={save}
            disabled={saving || !policy.can_divide && false}
            className="w-full bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-40"
          >
            {saving ? "Saving…" : "Save Division Policy"}
          </Button>
        </div>

        {/* Right: Readiness check */}
        <div className="space-y-4">
          <div className="rounded-lg border border-white/10 bg-neutral-900 p-4">
            <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider text-neutral-500">Gate Readiness Check</h4>
            {cells.length === 0 ? (
              <p className="text-xs text-neutral-600">No cells to check — create a cell first</p>
            ) : (
              <>
                <div className="mb-3">
                  <Label className="mb-1 text-[10px] uppercase tracking-wider text-neutral-600">Cell</Label>
                  <select
                    value={selectedCellId}
                    onChange={e => { setSelectedCellId(e.target.value); setReadiness(null); }}
                    className="w-full rounded-md border border-white/10 bg-neutral-800 px-2 py-1.5 text-xs text-neutral-300 focus:outline-none"
                  >
                    {cells.map(c => (
                      <option key={c.cell_id} value={c.cell_id}>
                        {c.cell_type} · gen {c.generation} · {c.lifecycle_state}
                      </option>
                    ))}
                  </select>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  className="w-full border-white/10 text-xs text-neutral-300"
                  onClick={checkReadiness}
                  disabled={checking || !selectedCellId}
                >
                  {checking ? "Checking gates…" : "Check Readiness"}
                </Button>
              </>
            )}
          </div>

          {readiness && (
            <div className="rounded-lg border border-white/10 bg-neutral-900 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-neutral-500">Result</h4>
                <Badge
                  variant="outline"
                  className={readiness.eligible
                    ? "border-emerald-400/30 text-emerald-300 text-[10px]"
                    : "border-red-400/30 text-red-300 text-[10px]"}
                >
                  {readiness.eligible ? "Eligible to divide" : `Blocked: ${readiness.blocked_by}`}
                </Badge>
              </div>

              {!readiness.policy_applied && (
                <p className="text-[11px] text-amber-400">No policy on genome — gates bypassed</p>
              )}

              <div className="space-y-2">
                <GateRow label="Load" result={readiness.load_gate} />
                <GateRow label="Capability" result={readiness.capability_gate} />
                <GateRow label="Lifecycle" result={readiness.lifecycle_gate} />
              </div>

              {readiness.eligible && (
                <div className="rounded-md border border-emerald-400/20 bg-emerald-400/5 px-3 py-2 text-xs text-emerald-300">
                  Recommended mode: <strong>{readiness.recommended_mode}</strong>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
