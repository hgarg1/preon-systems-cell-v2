"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { GenomeViewer } from "@/components/genome/genome-viewer";
import { DivisionPolicyEditor } from "@/components/genome/division-policy-editor";
import { useOrganismDetail } from "@/lib/organism-detail-context";
import type { Genome } from "@/lib/api";

export default function GenomePage() {
  const { detail, loading } = useOrganismDetail();
  const [genome, setGenome] = useState<Genome | null>(null);

  if (loading) return <div className="p-6 text-sm text-neutral-500">Loading genome…</div>;

  const activeGenome = genome ?? detail?.genome ?? null;

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="font-semibold text-white">Genome</h2>
        <p className="mt-0.5 text-sm text-neutral-500">
          The shared instruction set for all cells in this organism.
        </p>
      </div>

      {activeGenome ? (
        <Tabs defaultValue="structure">
          <TabsList className="mb-6">
            <TabsTrigger value="structure">Structure</TabsTrigger>
            <TabsTrigger value="division">Division Policy</TabsTrigger>
          </TabsList>

          <TabsContent value="structure">
            <GenomeViewer genome={activeGenome} />
          </TabsContent>

          <TabsContent value="division">
            <DivisionPolicyEditor
              genome={activeGenome}
              cells={detail?.cells ?? []}
              onSaved={setGenome}
            />
          </TabsContent>
        </Tabs>
      ) : (
        <p className="text-sm text-neutral-600">No genome attached to this organism</p>
      )}
    </div>
  );
}
