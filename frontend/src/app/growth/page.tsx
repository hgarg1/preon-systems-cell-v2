"use client";

import { Atom, FlaskConical, Sparkles } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { GenesisPanel } from "@/components/growth/genesis-panel";
import { PrimordialSoup } from "@/components/growth/primordial-soup";
import { ZygotePanel } from "@/components/growth/zygote-panel";
import { useOrganisms } from "@/lib/organisms-context";

export default function GrowthPage() {
  const { organisms, loading, refresh } = useOrganisms();

  if (loading) return <div className="p-8 text-sm text-neutral-500">Loading…</div>;

  const hasOrganisms = organisms.length > 0;
  const canReproduce = organisms.length >= 2;

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-2xl font-semibold text-white">Growth</h2>
        <p className="mt-1 text-sm text-neutral-400">
          Spark the first organism, provision its primordial environment, or reproduce existing organisms.
        </p>
      </div>

      <Tabs defaultValue={hasOrganisms ? "soup" : "genesis"}>
        <TabsList className="mb-6">
          <TabsTrigger value="genesis">
            <Atom className="mr-1.5 size-3.5" />
            Genesis
          </TabsTrigger>
          <TabsTrigger value="soup">
            <FlaskConical className="mr-1.5 size-3.5" />
            Primordial Soup
          </TabsTrigger>
          <TabsTrigger value="reproduction">
            <Sparkles className="mr-1.5 size-3.5" />
            Reproduction
          </TabsTrigger>
        </TabsList>

        <TabsContent value="genesis">
          <div className="mb-4 text-xs text-neutral-600">
            Create the first organism with no parents. Food and oxygen must be provisioned manually in the Primordial Soup tab.
          </div>
          <GenesisPanel onCreated={refresh} />
        </TabsContent>

        <TabsContent value="soup">
          <div className="mb-4 text-xs text-neutral-600">
            Pre-provision food and oxygen for an organism. Each food item carries a bundled oxygen allocation —
            compute is granted before food is delivered so the organism never eats without capacity to digest.
          </div>
          <PrimordialSoup organisms={organisms} />
        </TabsContent>

        <TabsContent value="reproduction">
          {canReproduce ? (
            <ZygotePanel organisms={organisms} onRefresh={refresh} />
          ) : (
            <div className="rounded-lg border border-dashed border-white/10 py-16 text-center">
              <p className="text-sm text-neutral-600">Reproduction requires at least two organisms</p>
              <p className="mt-1 text-xs text-neutral-700">
                {hasOrganisms ? "Create a second organism in Genesis" : "Start in Genesis to create your first organism"}
              </p>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
