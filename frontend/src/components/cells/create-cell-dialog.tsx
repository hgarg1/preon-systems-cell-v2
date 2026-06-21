"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createCell } from "@/lib/api";

export function CreateCellDialog({
  organismId,
  onCreated,
}: {
  organismId: string;
  onCreated: () => Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [tissueId, setTissueId] = useState("analysis");
  const [cellType, setCellType] = useState("specialist");
  const [busy, setBusy] = useState(false);

  async function handleCreate() {
    setBusy(true);
    try {
      await createCell(organismId, {
        tissueId,
        cellType,
        expressionProfile: { arithmetic: 0.2, reasoning: 0.95, calculator: 0.1 },
      });
      await onCreated();
      setOpen(false);
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <Button size="sm" onClick={() => setOpen(true)}>
        <Plus className="mr-1.5 size-3.5" />
        New Cell
      </Button>
    );
  }

  return (
    <div className="rounded-lg border border-white/10 bg-neutral-900 p-4">
      <h3 className="mb-3 text-sm font-medium text-neutral-200">Create Cell</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <Label htmlFor="tissue-id">Tissue ID</Label>
          <Input id="tissue-id" value={tissueId} onChange={(e) => setTissueId(e.target.value)} className="mt-1" />
        </div>
        <div>
          <Label htmlFor="cell-type">Cell Type</Label>
          <Input id="cell-type" value={cellType} onChange={(e) => setCellType(e.target.value)} className="mt-1" />
        </div>
      </div>
      <div className="mt-3 flex gap-2">
        <Button size="sm" onClick={handleCreate} disabled={busy}>{busy ? "Creating…" : "Create"}</Button>
        <Button size="sm" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
      </div>
    </div>
  );
}
