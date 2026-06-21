"use client";

import { Badge } from "@/components/ui/badge";
import type { SubmitSignalResponse } from "@/lib/api";

interface Stage {
  key: string;
  label: string;
  role: string;
  status: "pass" | "fail" | "warn" | "skip";
  outcome: string;
  details: [string, string][];
  raw?: Record<string, unknown>;
  colorClass: string;
  borderClass: string;
  bgClass: string;
}

function buildStages(response: SubmitSignalResponse): Stage[] {
  const stages: Stage[] = [];
  const { signal, membrane_decision, cell, protein, events, structure_request } = response;

  stages.push({
    key: "signal",
    label: "Signal",
    role: "Input",
    status: "pass",
    outcome: signal.type,
    details: [
      ["type", signal.type],
      ["priority", String(signal.priority)],
      ["id", signal.signal_id.slice(0, 12) + "…"],
    ],
    raw: signal.payload,
    colorClass: "text-blue-300",
    borderClass: "border-blue-400/30",
    bgClass: "bg-blue-400/5",
  });

  const memEvent = events.find((e) => e.type === "membrane");
  stages.push({
    key: "membrane",
    label: "Membrane",
    role: "Admission Control",
    status: membrane_decision.action === "accept" ? "pass" : "fail",
    outcome: membrane_decision.action === "accept" ? "ADMIT" : "REJECT",
    details: [
      ["decision", membrane_decision.action],
      ["code", membrane_decision.code],
      ["reason", membrane_decision.reason],
    ],
    raw: memEvent?.values,
    colorClass: "text-cyan-300",
    borderClass: "border-cyan-400/30",
    bgClass: "bg-cyan-400/5",
  });

  if (membrane_decision.action !== "accept") return stages;

  stages.push({
    key: "cytoplasm",
    label: "Cytoplasm",
    role: "Cell Selection",
    status: cell ? "pass" : "warn",
    outcome: cell ? "cell selected" : "no cell",
    details: cell
      ? [
          ["cell_id", cell.cell_id.slice(0, 12) + "…"],
          ["type", cell.cell_type],
          ["tissue", cell.tissue_id],
          ["health", String(cell.health_score)],
        ]
      : [["note", "no eligible cell found"]],
    colorClass: "text-slate-300",
    borderClass: "border-slate-400/30",
    bgClass: "bg-slate-400/5",
  });

  const nucleusEvent = events.find((e) => e.type === "nucleus");
  if (nucleusEvent) {
    stages.push({
      key: "nucleus",
      label: "Nucleus",
      role: "Module Selection",
      status: "pass",
      outcome: "module selected",
      details: [["message", nucleusEvent.message]],
      raw: nucleusEvent.values,
      colorClass: "text-violet-300",
      borderClass: "border-violet-400/30",
      bgClass: "bg-violet-400/5",
    });
  }

  const mitoEvent = events.find((e) => e.type === "mitochondria");
  if (mitoEvent) {
    stages.push({
      key: "mitochondria",
      label: "Mitochondria",
      role: "Budget Allocation",
      status: "pass",
      outcome: "budget reserved",
      details: [["message", mitoEvent.message]],
      raw: mitoEvent.values,
      colorClass: "text-amber-300",
      borderClass: "border-amber-400/30",
      bgClass: "bg-amber-400/5",
    });
  }

  const riboEvent = events.find((e) => e.type === "ribosome");
  if (riboEvent) {
    stages.push({
      key: "ribosome",
      label: "Ribosome",
      role: "Execution",
      status: "pass",
      outcome: "executed",
      details: [["message", riboEvent.message]],
      raw: riboEvent.values,
      colorClass: "text-emerald-300",
      borderClass: "border-emerald-400/30",
      bgClass: "bg-emerald-400/5",
    });
  }

  if (protein) {
    const proteinStatus =
      protein.status === "approved" ? "pass"
      : protein.status === "dropped" || protein.status === "blocked" ? "fail"
      : "warn";
    stages.push({
      key: "protein",
      label: "Protein",
      role: "Output",
      status: proteinStatus,
      outcome: protein.status,
      details: [
        ["status", protein.status],
        ["confidence", protein.confidence.toFixed(3)],
        ["type", protein.type],
      ],
      raw: protein.payload,
      colorClass: "text-purple-300",
      borderClass: "border-purple-400/30",
      bgClass: "bg-purple-400/5",
    });

    const vr = protein.validation_report;
    stages.push({
      key: "golgi",
      label: "Golgi",
      role: "Validation",
      status: vr.valid ? "pass" : vr.repaired ? "warn" : "fail",
      outcome: vr.valid ? "valid" : vr.repaired ? "repaired" : "invalid",
      details: [
        ["valid", String(vr.valid)],
        ["repaired", String(vr.repaired)],
        ["misfolding", vr.misfolding_types.join(", ") || "none"],
        ...(vr.errors.length ? [["errors", vr.errors.join("; ")] as [string, string]] : []),
      ],
      colorClass: "text-orange-300",
      borderClass: "border-orange-400/30",
      bgClass: "bg-orange-400/5",
    });
  }

  if (structure_request) {
    stages.push({
      key: "skeleton",
      label: "Skeleton",
      role: "Structure Request",
      status: "warn",
      outcome: "request emitted",
      details: [
        ["contract", structure_request.requested_contract],
        ["reason", structure_request.reason],
      ],
      colorClass: "text-pink-300",
      borderClass: "border-pink-400/30",
      bgClass: "bg-pink-400/5",
    });
  }

  return stages;
}

function statusIcon(status: Stage["status"]): string {
  switch (status) {
    case "pass": return "✓";
    case "fail": return "✗";
    case "warn": return "⚠";
    default:     return "○";
  }
}

function statusColor(status: Stage["status"]): string {
  switch (status) {
    case "pass": return "text-green-400";
    case "fail": return "text-red-400";
    case "warn": return "text-amber-400";
    default:     return "text-neutral-500";
  }
}

export function PipelineTrace({ response }: { response: SubmitSignalResponse }) {
  const stages = buildStages(response);

  return (
    <div className="space-y-0">
      {stages.map((stage, i) => (
        <div key={stage.key} className="relative">
          {/* Connector line */}
          {i < stages.length - 1 ? (
            <div className="absolute left-[1.5rem] top-full z-10 h-3 w-px bg-white/10" />
          ) : null}

          <div className={`rounded-lg border p-3 ${stage.borderClass} ${stage.bgClass} mb-3`}>
            <div className="flex items-start gap-3">
              {/* Status indicator */}
              <span className={`mt-0.5 flex-shrink-0 font-mono text-base leading-none ${statusColor(stage.status)}`}>
                {statusIcon(stage.status)}
              </span>

              <div className="min-w-0 flex-1">
                {/* Stage header */}
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`text-xs font-semibold uppercase tracking-wider ${stage.colorClass}`}>
                    {stage.label}
                  </span>
                  <span className="text-xs text-neutral-600">—</span>
                  <span className="text-xs text-neutral-500">{stage.role}</span>
                  <Badge
                    variant="outline"
                    className={`ml-auto text-[10px] px-1.5 py-0 ${stage.borderClass} ${stage.colorClass}`}
                  >
                    {stage.outcome}
                  </Badge>
                </div>

                {/* Key-value details */}
                <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs">
                  {stage.details.map(([k, v]) => (
                    <div key={k} className="flex gap-1.5 min-w-0">
                      <span className="flex-shrink-0 text-neutral-600">{k}:</span>
                      <span className="truncate text-neutral-300">{v}</span>
                    </div>
                  ))}
                </div>

                {/* Raw payload (collapsed) */}
                {stage.raw && Object.keys(stage.raw).length > 0 ? (
                  <details className="mt-2">
                    <summary className="cursor-pointer text-[10px] text-neutral-600 hover:text-neutral-400">
                      payload
                    </summary>
                    <pre className="mt-1 max-h-24 overflow-auto rounded bg-black/30 p-2 text-[10px] text-neutral-400">
                      {JSON.stringify(stage.raw, null, 2)}
                    </pre>
                  </details>
                ) : null}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
