"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createMemory } from "@/lib/api";

export function CreateMemoryDialog({
  organismId,
  onCreated,
}: {
  organismId: string;
  onCreated: () => Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [scope, setScope] = useState("organism");
  const [kind, setKind] = useState("note");
  const [content, setContent] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate() {
    let payload: Record<string, unknown>;
    try {
      payload = content.trim().startsWith("{") ? JSON.parse(content) : { note: content };
    } catch {
      setError("Content must be valid JSON or plain text");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await createMemory(organismId, { scope, kind, payload });
      await onCreated();
      setOpen(false);
      setContent("");
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <Button size="sm" onClick={() => setOpen(true)}>
        <Plus className="mr-1.5 size-3.5" />
        New Memory
      </Button>
    );
  }

  return (
    <div className="rounded-lg border border-white/10 bg-neutral-900 p-4">
      <h3 className="mb-3 text-sm font-medium text-neutral-200">Create Memory Record</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <Label htmlFor="mem-scope">Scope</Label>
          <Input id="mem-scope" value={scope} onChange={(e) => setScope(e.target.value)} className="mt-1" />
        </div>
        <div>
          <Label htmlFor="mem-kind">Kind</Label>
          <Input id="mem-kind" value={kind} onChange={(e) => setKind(e.target.value)} className="mt-1" />
        </div>
      </div>
      <div className="mt-3">
        <Label htmlFor="mem-content">Content (JSON or plain text)</Label>
        <textarea
          id="mem-content"
          className="mt-1 h-24 w-full rounded-md border border-white/10 bg-neutral-950 p-2 font-mono text-sm text-neutral-100 outline-none focus:border-emerald-400/50"
          value={content}
          onChange={(e) => setContent(e.target.value)}
        />
      </div>
      {error ? <p className="mt-2 text-xs text-red-400">{error}</p> : null}
      <div className="mt-3 flex gap-2">
        <Button size="sm" onClick={handleCreate} disabled={busy}>{busy ? "Saving…" : "Save"}</Button>
        <Button size="sm" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
      </div>
    </div>
  );
}
