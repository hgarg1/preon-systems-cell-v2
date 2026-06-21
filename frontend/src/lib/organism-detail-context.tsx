"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { type OrganismDetail, getOrganism } from "@/lib/api";

interface OrganismDetailContextValue {
  detail: OrganismDetail | null;
  loading: boolean;
  refresh: () => Promise<void>;
}

const OrganismDetailContext = createContext<OrganismDetailContextValue | null>(null);

export function OrganismDetailProvider({ id, children }: { id: string; children: React.ReactNode }) {
  const [detail, setDetail] = useState<OrganismDetail | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const d = await getOrganism(id);
    setDetail(d);
  }, [id]);

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, [refresh]);

  return (
    <OrganismDetailContext.Provider value={{ detail, loading, refresh }}>
      {children}
    </OrganismDetailContext.Provider>
  );
}

export function useOrganismDetail() {
  const ctx = useContext(OrganismDetailContext);
  if (!ctx) throw new Error("useOrganismDetail must be used within OrganismDetailProvider");
  return ctx;
}
