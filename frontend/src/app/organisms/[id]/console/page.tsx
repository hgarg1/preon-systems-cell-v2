"use client";

import { use, useState } from "react";
import { Braces, ShieldAlert, ShieldCheck, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PipelineTrace } from "@/components/console/pipeline-trace";
import { useOrganismDetail } from "@/lib/organism-detail-context";
import { submitSignal } from "@/lib/api";
import type { SubmitSignalResponse } from "@/lib/api";

const SIGNAL_PRESETS = [
  { label: "calculate", payload: '{ "expression": "2 + 2" }' },
  { label: "ping",      payload: '{}' },
  { label: "query",     payload: '{ "question": "What is the current state?" }' },
];

export default function ConsolePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { refresh } = useOrganismDetail();
  const [signalType, setSignalType] = useState("calculate");
  const [payloadText, setPayloadText] = useState('{ "expression": "2 + 2" }');
  const [priority, setPriority] = useState("5");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<SubmitSignalResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  function applyPreset(preset: typeof SIGNAL_PRESETS[number]) {
    setSignalType(preset.label);
    setPayloadText(preset.payload);
  }

  async function handleSubmit() {
    let payload: Record<string, unknown>;
    try {
      payload = JSON.parse(payloadText);
    } catch {
      setError("Payload must be valid JSON");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const response = await submitSignal(id, {
        type: signalType,
        payload,
        priority: Number(priority) || 5,
      });
      setResult(response);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signal submission failed");
    } finally {
      setSubmitting(false);
    }
  }

  const admitted = result?.membrane_decision.action === "accept";

  return (
    <div className="grid h-full grid-cols-1 gap-0 lg:grid-cols-[380px_1fr]">
      {/* Left: Signal form */}
      <div className="flex flex-col gap-5 border-r border-white/10 p-6">
        {/* Presets */}
        <div>
          <p className="mb-2 text-xs text-neutral-500">Presets</p>
          <div className="flex flex-wrap gap-1.5">
            {SIGNAL_PRESETS.map((p) => (
              <button
                key={p.label}
                onClick={() => applyPreset(p)}
                className={`rounded-md border px-2.5 py-1 text-xs transition-colors ${
                  signalType === p.label
                    ? "border-emerald-400/40 bg-emerald-400/10 text-emerald-300"
                    : "border-white/10 text-neutral-400 hover:border-white/20 hover:text-neutral-200"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Signal type */}
        <div>
          <Label htmlFor="signal-type">Signal type</Label>
          <Input
            id="signal-type"
            value={signalType}
            onChange={(e) => setSignalType(e.target.value)}
            className="mt-1.5 font-mono"
            placeholder="calculate"
          />
        </div>

        {/* Payload */}
        <div className="flex-1">
          <Label htmlFor="payload">Payload JSON</Label>
          <textarea
            id="payload"
            className="mt-1.5 h-48 w-full resize-none rounded-md border border-white/10 bg-neutral-950 p-3 font-mono text-sm text-neutral-100 outline-none focus:border-emerald-400/50"
            value={payloadText}
            onChange={(e) => setPayloadText(e.target.value)}
            spellCheck={false}
          />
        </div>

        {/* Priority */}
        <div>
          <Label htmlFor="priority">Priority (1–10)</Label>
          <Input
            id="priority"
            type="number"
            min="1"
            max="10"
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            className="mt-1.5 w-24"
          />
        </div>

        {error ? (
          <p className="rounded-md border border-red-400/30 bg-red-400/10 px-3 py-2 text-sm text-red-300">{error}</p>
        ) : null}

        <Button onClick={handleSubmit} disabled={submitting || !id} className="w-full">
          <Sparkles className="mr-2 size-4" />
          {submitting ? "Submitting…" : "Submit Signal"}
        </Button>

        {/* Membrane decision quick result */}
        {result ? (
          <div className={`rounded-md border px-3 py-2.5 text-sm ${
            admitted
              ? "border-emerald-400/30 bg-emerald-400/5 text-emerald-200"
              : "border-red-400/30 bg-red-400/5 text-red-200"
          }`}>
            <div className="flex items-center gap-2">
              {admitted
                ? <ShieldCheck className="size-4 flex-shrink-0 text-emerald-400" />
                : <ShieldAlert className="size-4 flex-shrink-0 text-red-400" />
              }
              <span className="font-medium">{result.membrane_decision.action.toUpperCase()}</span>
              <Badge variant="outline" className="ml-auto text-[10px]">{result.membrane_decision.code}</Badge>
            </div>
            <p className="mt-1 text-xs text-neutral-400">{result.membrane_decision.reason}</p>
          </div>
        ) : null}

        {/* Latest protein summary */}
        {result?.protein ? (
          <div className="rounded-md border border-purple-400/20 bg-purple-400/5 p-3">
            <div className="mb-2 flex items-center gap-2">
              <Braces className="size-4 text-purple-400" />
              <span className="text-xs font-medium text-purple-300">Latest Protein</span>
              <Badge variant="outline" className="ml-auto text-[10px] border-purple-400/30 text-purple-300">
                {result.protein.status}
              </Badge>
            </div>
            <div className="text-xs text-neutral-500">
              confidence: {result.protein.confidence.toFixed(3)}
            </div>
            {result.protein.validation_report.misfolding_types.length ? (
              <div className="mt-1 flex flex-wrap gap-1">
                {result.protein.validation_report.misfolding_types.map((t) => (
                  <Badge key={t} variant="outline" className="text-[10px] border-amber-400/30 text-amber-300">{t}</Badge>
                ))}
              </div>
            ) : null}
            <pre className="mt-2 max-h-24 overflow-auto rounded bg-black/30 p-2 text-[10px] text-neutral-300">
              {JSON.stringify(result.protein.payload, null, 2)}
            </pre>
          </div>
        ) : null}

        {result?.structure_request ? (
          <div className="rounded-md border border-pink-400/30 bg-pink-400/5 px-3 py-2 text-sm">
            <p className="text-xs text-pink-300">
              Structure request: <span className="font-mono">{result.structure_request.requested_contract}</span>
            </p>
          </div>
        ) : null}
      </div>

      {/* Right: Pipeline trace */}
      <div className="p-6">
        <p className="mb-4 text-sm font-medium text-neutral-400">
          {result ? "Execution Pipeline" : "Submit a signal to see the execution pipeline"}
        </p>
        {result ? (
          <PipelineTrace response={result} />
        ) : (
          <div className="flex h-64 items-center justify-center rounded-lg border border-dashed border-white/10">
            <p className="text-sm text-neutral-600">
              Signal → Membrane → Cytoplasm → Nucleus → Ribosome → Protein → Golgi
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
