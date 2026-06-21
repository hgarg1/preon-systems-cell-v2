"use client";

import { use } from "react";
import { CellTable } from "@/components/cells/cell-table";
import { CreateCellDialog } from "@/components/cells/create-cell-dialog";
import { useOrganismDetail } from "@/lib/organism-detail-context";

export default function CellsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { detail, loading, refresh } = useOrganismDetail();

  if (loading) return <div className="p-6 text-sm text-neutral-500">Loading cells…</div>;

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between gap-4">
        <div>
          <h2 className="font-semibold text-white">Cells</h2>
          <p className="mt-0.5 text-sm text-neutral-500">
            Execution units assigned to this organism. Each cell has its own tissue, expression profile, and resource budget.
          </p>
        </div>
        <CreateCellDialog organismId={id} onCreated={refresh} />
      </div>
      <CellTable cells={detail?.cells ?? []} />
    </div>
  );
}
