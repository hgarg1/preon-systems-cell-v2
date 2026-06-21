"use client";

import { use } from "react";
import { MemoryTable } from "@/components/memory/memory-table";
import { CreateMemoryDialog } from "@/components/memory/create-memory-dialog";
import { useOrganismDetail } from "@/lib/organism-detail-context";

export default function MemoryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { detail, loading, refresh } = useOrganismDetail();

  if (loading) return <div className="p-6 text-sm text-neutral-500">Loading memory…</div>;

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between gap-4">
        <div>
          <h2 className="font-semibold text-white">Memory</h2>
          <p className="mt-0.5 text-sm text-neutral-500">
            Persistent records the organism retains across hibernation cycles. Scoped by kind and confidence.
          </p>
        </div>
        <CreateMemoryDialog organismId={id} onCreated={refresh} />
      </div>
      <MemoryTable records={detail?.memory_records ?? []} />
    </div>
  );
}
