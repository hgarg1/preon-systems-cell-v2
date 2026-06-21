"use client";

import { useCallback, useEffect, useState } from "react";
import { Cable, ShieldAlert } from "lucide-react";
import { ContractTable } from "@/components/contracts/contract-table";
import { CreateContractDialog } from "@/components/contracts/create-contract-dialog";
import { StructureQueue } from "@/components/contracts/structure-queue";
import { listContracts, listStructureRequests } from "@/lib/api";
import type { Contract, StructureRequest } from "@/lib/api";

export default function ContractsPage() {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [requests, setRequests] = useState<StructureRequest[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const [c, r] = await Promise.all([listContracts(), listStructureRequests()]);
    setContracts(c);
    setRequests(r);
  }, []);

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, [refresh]);

  if (loading) return <div className="p-8 text-sm text-neutral-500">Loading contracts…</div>;

  const openRequests = requests.filter((r) => r.status === "open");

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-2xl font-semibold text-white">Contracts</h2>
        <p className="mt-1 text-sm text-neutral-400">
          The skeletal layer. Contracts define how cells access external services and capabilities.
        </p>
      </div>

      {/* Active contracts */}
      <section className="mb-10">
        <div className="mb-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Cable className="size-4 text-pink-400" />
            <h3 className="font-medium text-white">Contract Registry</h3>
            <span className="text-xs text-neutral-600">{contracts.length} total</span>
          </div>
          <CreateContractDialog onCreated={refresh} />
        </div>
        <ContractTable contracts={contracts} onRefresh={refresh} />
      </section>

      {/* Structure requests */}
      <section>
        <div className="mb-4 flex items-center gap-2">
          <ShieldAlert className="size-4 text-amber-400" />
          <h3 className="font-medium text-white">Structure Requests</h3>
          {openRequests.length > 0 ? (
            <span className="rounded-full bg-amber-400/20 px-2 py-0.5 text-xs text-amber-300">
              {openRequests.length} open
            </span>
          ) : null}
        </div>
        <p className="mb-4 text-sm text-neutral-500">
          Cells emit these when they need a contract that doesn't exist. Resolve by creating the contract, or block if invalid.
        </p>
        <StructureQueue requests={requests} onRefresh={refresh} />
      </section>
    </div>
  );
}
