"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createContract } from "@/lib/api";

export function CreateContractDialog({ onCreated }: { onCreated: () => Promise<void> }) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [actions, setActions] = useState("");
  const [schema, setSchema] = useState('{ "input": {}, "output": {} }');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate() {
    let parsedSchema: Record<string, unknown> = {};
    try {
      parsedSchema = JSON.parse(schema);
    } catch {
      setError("Schema must be valid JSON");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await createContract({
        name: name.trim(),
        allowedActions: actions.split(",").map((a) => a.trim()).filter(Boolean),
        schema: parsedSchema,
      });
      await onCreated();
      setOpen(false);
      setName("");
      setActions("");
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <Button size="sm" onClick={() => setOpen(true)}>
        <Plus className="mr-1.5 size-3.5" />
        New Contract
      </Button>
    );
  }

  return (
    <div className="rounded-lg border border-white/10 bg-neutral-900 p-5">
      <h3 className="mb-4 text-sm font-medium text-neutral-200">Register Contract</h3>
      <div className="grid gap-4">
        <div>
          <Label htmlFor="contract-name">Name (dot-notation)</Label>
          <Input
            id="contract-name"
            placeholder="CustomerProfileService.getByUserId"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 font-mono"
          />
        </div>
        <div>
          <Label htmlFor="contract-actions">Allowed Actions (comma-separated)</Label>
          <Input
            id="contract-actions"
            placeholder="read_profile, update_profile"
            value={actions}
            onChange={(e) => setActions(e.target.value)}
            className="mt-1"
          />
        </div>
        <div>
          <Label htmlFor="contract-schema">Schema JSON</Label>
          <textarea
            id="contract-schema"
            className="mt-1 h-20 w-full rounded-md border border-white/10 bg-neutral-950 p-2 font-mono text-sm text-neutral-100 outline-none focus:border-emerald-400/50"
            value={schema}
            onChange={(e) => setSchema(e.target.value)}
          />
        </div>
      </div>
      {error ? <p className="mt-2 text-xs text-red-400">{error}</p> : null}
      <div className="mt-4 flex gap-2">
        <Button size="sm" onClick={handleCreate} disabled={busy || !name.trim()}>
          {busy ? "Registering…" : "Register"}
        </Button>
        <Button size="sm" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
      </div>
    </div>
  );
}
