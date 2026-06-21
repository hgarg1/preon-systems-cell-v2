"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { type HealthResponse, type OrganismRecord, getHealth, listOrganisms } from "@/lib/api";

interface OrganismsContextValue {
  organisms: OrganismRecord[];
  health: HealthResponse | null;
  loading: boolean;
  refresh: () => Promise<void>;
}

const OrganismsContext = createContext<OrganismsContextValue | null>(null);

export function OrganismsProvider({ children }: { children: React.ReactNode }) {
  const [organisms, setOrganisms] = useState<OrganismRecord[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const [runtimeHealth, list] = await Promise.all([getHealth(), listOrganisms()]);
      setHealth(runtimeHealth);
      setOrganisms(list);
    } catch {
      // SessionWatchdog handles redirecting unauthenticated users to /login.
    }
  }, []);

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, [refresh]);

  return (
    <OrganismsContext.Provider value={{ organisms, health, loading, refresh }}>
      {children}
    </OrganismsContext.Provider>
  );
}

export function useOrganisms() {
  const ctx = useContext(OrganismsContext);
  if (!ctx) throw new Error("useOrganisms must be used within OrganismsProvider");
  return ctx;
}
