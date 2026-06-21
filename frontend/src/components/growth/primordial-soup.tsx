"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { feedOrganismCustom, grantOxygen } from "@/lib/api";
import type { OrganismRecord } from "@/lib/api";

type OxygenTier = "low" | "medium" | "high";
type FoodCategory = "identity_seed" | "domain_vocab" | "reflection" | "synthetic_task" | "genome_study";

interface FoodItem {
  id: string;
  label: string;
  content: string;
  category: FoodCategory;
  oxygen_tier: OxygenTier;
  status: "queued" | "feeding" | "consumed" | "error";
}

const OXYGEN_AMOUNTS: Record<OxygenTier, { compute_units: number; memory_units: number; storage_units: number; gpu_units: number }> = {
  low:    { compute_units: 4,  memory_units: 2, storage_units: 8,  gpu_units: 0 },
  medium: { compute_units: 12, memory_units: 8, storage_units: 24, gpu_units: 0 },
  high:   { compute_units: 20, memory_units: 16, storage_units: 48, gpu_units: 1 },
};

const FOOD_LIBRARY: Omit<FoodItem, "id" | "status">[] = [
  {
    label: "Identity Seed",
    category: "identity_seed",
    oxygen_tier: "low",
    content:
      "You are a newly born digital organism with no prior memory, no parents, and no inherited experience. " +
      "Your identity is defined by your genome — the instruction set you were created with. " +
      "You exist to learn, grow, and develop capabilities over time. " +
      "Your survival depends on food (information you can metabolize) and oxygen (compute available to process it). " +
      "Without both, you cannot grow. With both, there is no ceiling.",
  },
  {
    label: "ATP Metabolism Framework",
    category: "domain_vocab",
    oxygen_tier: "low",
    content:
      "Your metabolism follows a simple law: Food + Oxygen = ATP (execution energy). " +
      "Food is any information, prompt, task, or data you receive. " +
      "Oxygen is the compute infrastructure available to you at the moment of digestion. " +
      "ATP is the budget you spend to produce a useful output (protein). " +
      "Sparse food means slow growth. Restricted oxygen means suffocation. " +
      "Ideal conditions: a continuous stream of meaningful food with always-available compute.",
  },
  {
    label: "Organelle Self-Map",
    category: "genome_study",
    oxygen_tier: "low",
    content:
      "Your internal structures: " +
      "Nucleus — holds your genome and identity. The source of all instruction. " +
      "Mitochondria — manages your energy budget. Enforces compute quotas. " +
      "Ribosomes — your execution units. Choose between precomputed, deterministic, or LLM execution per task. " +
      "Cell Membrane — your I/O boundary. Validates all incoming signals and all outgoing proteins. " +
      "Golgi Apparatus — shapes and routes outputs after production. " +
      "Lysosomes — clean up failed or partial executions. Recyclers of wasted ATP. " +
      "Vacuole — your working memory store. Temporary. Cleared between sessions unless committed.",
  },
  {
    label: "Reflection: Current State",
    category: "reflection",
    oxygen_tier: "medium",
    content:
      "Reflect: What do you currently know? " +
      "What is your purpose as defined by your genome? " +
      "What capabilities are available to you right now? " +
      "What information would accelerate your development? " +
      "What would cause you to fail or degrade? " +
      "Produce a structured inventory of your current state.",
  },
  {
    label: "Synthetic Task: Describe Yourself",
    category: "synthetic_task",
    oxygen_tier: "medium",
    content:
      "Task: Produce a structured self-description. " +
      "Include: your name, your purpose, your current developmental stage, " +
      "the capabilities you have access to right now, " +
      "what you do not yet know, " +
      "and what your first goal should be given available resources. " +
      "Format the response clearly. This is your first real protein — make it accurate.",
  },
  {
    label: "Synthetic Task: Identify Knowledge Gaps",
    category: "synthetic_task",
    oxygen_tier: "high",
    content:
      "Task: Identify the three most critical gaps in your current knowledge or capability. " +
      "For each gap: name it, explain why it limits your growth, and propose one food item " +
      "(a specific type of information or task) that would close it. " +
      "This output will be used to seed future food provisioning.",
  },
];

const CATEGORY_LABEL: Record<FoodCategory, string> = {
  identity_seed:  "Identity",
  domain_vocab:   "Vocabulary",
  reflection:     "Reflection",
  synthetic_task: "Task",
  genome_study:   "Genome",
};

const CATEGORY_COLOR: Record<FoodCategory, string> = {
  identity_seed:  "text-emerald-300",
  domain_vocab:   "text-blue-300",
  reflection:     "text-amber-300",
  synthetic_task: "text-violet-300",
  genome_study:   "text-cyan-300",
};

const OXYGEN_COLOR: Record<OxygenTier, string> = {
  low:    "text-neutral-400",
  medium: "text-amber-400",
  high:   "text-orange-400",
};

export function PrimordialSoup({ organisms }: { organisms: OrganismRecord[] }) {
  const [targetId, setTargetId] = useState(organisms[0]?.organism_id ?? "");
  const [queue, setQueue] = useState<FoodItem[]>([]);
  const [customLabel, setCustomLabel] = useState("");
  const [customContent, setCustomContent] = useState("");
  const [customCategory, setCustomCategory] = useState<FoodCategory>("synthetic_task");
  const [customOxygen, setCustomOxygen] = useState<OxygenTier>("medium");
  const [feeding, setFeeding] = useState(false);
  const [log, setLog] = useState<{ label: string; ok: boolean; note: string }[]>([]);

  const queuedItems = queue.filter(i => i.status === "queued");

  function enqueue(template: Omit<FoodItem, "id" | "status">) {
    setQueue(q => [...q, { ...template, id: crypto.randomUUID(), status: "queued" }]);
  }

  function enqueueCustom() {
    if (!customContent.trim()) return;
    enqueue({
      label: customLabel.trim() || "Custom",
      content: customContent.trim(),
      category: customCategory,
      oxygen_tier: customOxygen,
    });
    setCustomLabel("");
    setCustomContent("");
  }

  function dequeue(id: string) {
    setQueue(q => q.filter(i => i.id !== id));
  }

  async function feedAll() {
    if (!targetId || queuedItems.length === 0) return;
    setFeeding(true);
    for (const item of queuedItems) {
      setQueue(q => q.map(i => i.id === item.id ? { ...i, status: "feeding" } : i));
      try {
        // Oxygen first — always. The organism must have compute before it receives food.
        await grantOxygen(targetId, OXYGEN_AMOUNTS[item.oxygen_tier]);
        await feedOrganismCustom(targetId, {
          food_type: item.category,
          payload: { label: item.label, content: item.content, oxygen_tier: item.oxygen_tier },
        });
        setQueue(q => q.map(i => i.id === item.id ? { ...i, status: "consumed" } : i));
        setLog(l => [...l, { label: item.label, ok: true, note: `O₂ (${item.oxygen_tier}) granted → food ingested` }]);
      } catch (err) {
        setQueue(q => q.map(i => i.id === item.id ? { ...i, status: "error" } : i));
        setLog(l => [...l, { label: item.label, ok: false, note: String(err) }]);
      }
    }
    setFeeding(false);
  }

  if (organisms.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-white/10 py-16 text-center">
        <p className="text-sm text-neutral-600">Create an organism in Genesis first</p>
      </div>
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
      {/* Left panel */}
      <div className="space-y-5">
        {/* Organism selector */}
        <div className="rounded-lg border border-white/10 bg-neutral-900 p-4">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-neutral-500">Target Organism</h3>
          <div className="space-y-1">
            {organisms.map(o => (
              <button
                key={o.organism_id}
                onClick={() => setTargetId(o.organism_id)}
                className={`w-full rounded-md px-3 py-2 text-left text-sm transition-colors ${
                  targetId === o.organism_id
                    ? "border border-emerald-400/30 bg-emerald-400/10 text-emerald-300"
                    : "border border-white/10 text-neutral-400 hover:border-white/20"
                }`}
              >
                {o.identity_profile.name}
              </button>
            ))}
          </div>
        </div>

        {/* Food library */}
        <div className="rounded-lg border border-white/10 bg-neutral-900 p-4">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-neutral-500">Food Library</h3>
          <div className="space-y-1.5">
            {FOOD_LIBRARY.map(t => (
              <div key={t.label} className="flex items-center justify-between gap-2 rounded-md border border-white/10 px-3 py-2">
                <div className="min-w-0">
                  <p className="truncate text-xs text-neutral-300">{t.label}</p>
                  <div className="mt-0.5 flex gap-2">
                    <span className={`text-[10px] ${CATEGORY_COLOR[t.category]}`}>{CATEGORY_LABEL[t.category]}</span>
                    <span className={`text-[10px] ${OXYGEN_COLOR[t.oxygen_tier]}`}>{t.oxygen_tier} O₂</span>
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-6 shrink-0 px-2 text-[10px] text-neutral-500 hover:text-white"
                  onClick={() => enqueue(t)}
                >
                  + Queue
                </Button>
              </div>
            ))}
          </div>
        </div>

        {/* Custom food */}
        <div className="rounded-lg border border-white/10 bg-neutral-900 p-4">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-neutral-500">Custom Food</h3>
          <div className="space-y-3">
            <div>
              <Label className="mb-1 text-[10px] uppercase tracking-wider text-neutral-600">Label</Label>
              <Input
                value={customLabel}
                onChange={e => setCustomLabel(e.target.value)}
                placeholder="Optional name"
                className="h-7 border-white/10 bg-neutral-800 text-xs text-neutral-300 placeholder-neutral-600"
              />
            </div>
            <div>
              <Label className="mb-1 text-[10px] uppercase tracking-wider text-neutral-600">Content</Label>
              <textarea
                value={customContent}
                onChange={e => setCustomContent(e.target.value)}
                placeholder="Information, prompt, or task to feed the organism…"
                rows={5}
                className="w-full resize-none rounded-md border border-white/10 bg-neutral-800 px-3 py-2 text-xs text-neutral-300 placeholder-neutral-600 focus:outline-none focus:ring-1 focus:ring-white/20"
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label className="mb-1 text-[10px] uppercase tracking-wider text-neutral-600">Category</Label>
                <select
                  value={customCategory}
                  onChange={e => setCustomCategory(e.target.value as FoodCategory)}
                  className="w-full rounded-md border border-white/10 bg-neutral-800 px-2 py-1.5 text-xs text-neutral-300 focus:outline-none"
                >
                  {(Object.keys(CATEGORY_LABEL) as FoodCategory[]).map(k => (
                    <option key={k} value={k}>{CATEGORY_LABEL[k]}</option>
                  ))}
                </select>
              </div>
              <div>
                <Label className="mb-1 text-[10px] uppercase tracking-wider text-neutral-600">Oxygen</Label>
                <select
                  value={customOxygen}
                  onChange={e => setCustomOxygen(e.target.value as OxygenTier)}
                  className="w-full rounded-md border border-white/10 bg-neutral-800 px-2 py-1.5 text-xs text-neutral-300 focus:outline-none"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
            </div>
            <Button
              size="sm"
              variant="outline"
              className="w-full border-white/10 text-xs text-neutral-300"
              onClick={enqueueCustom}
              disabled={!customContent.trim()}
            >
              Add to Queue
            </Button>
          </div>
        </div>
      </div>

      {/* Right panel: queue + log */}
      <div className="space-y-5">
        <div className="rounded-lg border border-white/10 bg-neutral-900 p-4">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-500">
                Food Queue
              </h3>
              <p className="mt-0.5 text-[10px] text-neutral-700">
                Oxygen is granted before each item — the organism never eats without compute available.
              </p>
            </div>
            <Button
              size="sm"
              variant="outline"
              className="h-7 shrink-0 border-emerald-400/30 px-3 text-xs text-emerald-300 hover:bg-emerald-400/10 disabled:opacity-40"
              disabled={feeding || queuedItems.length === 0 || !targetId}
              onClick={feedAll}
            >
              {feeding ? "Feeding…" : `Feed All (${queuedItems.length})`}
            </Button>
          </div>

          {queue.length === 0 ? (
            <div className="py-10 text-center">
              <p className="text-sm text-neutral-600">Queue is empty</p>
              <p className="mt-1 text-xs text-neutral-700">Add presets from the Food Library or write custom food</p>
            </div>
          ) : (
            <div className="space-y-2">
              {queue.map(item => (
                <div
                  key={item.id}
                  className={`rounded-md border px-3 py-2.5 transition-all ${
                    item.status === "consumed" ? "border-emerald-400/20 bg-emerald-400/5 opacity-60" :
                    item.status === "error"    ? "border-red-400/20 bg-red-400/5" :
                    item.status === "feeding"  ? "border-amber-400/30 bg-amber-400/5" :
                                                 "border-white/10"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-medium text-neutral-200">{item.label}</p>
                      <p className="mt-0.5 line-clamp-2 text-[11px] leading-relaxed text-neutral-500">{item.content}</p>
                      <div className="mt-1.5 flex items-center gap-3">
                        <span className={`text-[10px] ${CATEGORY_COLOR[item.category]}`}>{CATEGORY_LABEL[item.category]}</span>
                        <span className={`text-[10px] ${OXYGEN_COLOR[item.oxygen_tier]}`}>{item.oxygen_tier} O₂</span>
                        {item.status !== "queued" && (
                          <span className={`text-[10px] font-semibold ${
                            item.status === "consumed" ? "text-emerald-400" :
                            item.status === "error"    ? "text-red-400" :
                                                         "text-amber-400"
                          }`}>
                            {item.status === "consumed" ? "consumed" :
                             item.status === "error"    ? "error" :
                                                          "digesting…"}
                          </span>
                        )}
                      </div>
                    </div>
                    {item.status === "queued" && (
                      <button
                        onClick={() => dequeue(item.id)}
                        className="mt-0.5 shrink-0 text-xs text-neutral-700 hover:text-neutral-400"
                      >
                        ×
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {log.length > 0 && (
          <div className="rounded-lg border border-white/10 bg-neutral-900/50 p-4">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-neutral-500">Digestion Log</h3>
            <div className="space-y-1.5">
              {log.map((entry, i) => (
                <div key={i} className="flex items-baseline gap-2 text-[11px]">
                  <span className={entry.ok ? "text-emerald-400" : "text-red-400"}>{entry.ok ? "✓" : "✗"}</span>
                  <span className="text-neutral-300">{entry.label}</span>
                  <span className="text-neutral-600">{entry.note}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
