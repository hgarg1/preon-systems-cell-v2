"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Brain, Database, Moon, Puzzle, Terminal, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useOrganismDetail } from "@/lib/organism-detail-context";
import { useOrganisms } from "@/lib/organisms-context";
import { hibernateOrganism, wakeOrganism } from "@/lib/api";
import { useState } from "react";
import type { LifecycleState } from "@/lib/api";

function lifecycleBadge(state: LifecycleState): string {
  switch (state) {
    case "active":     return "border-green-400/40 bg-green-400/10 text-green-300";
    case "hibernated": return "border-yellow-400/40 bg-yellow-400/10 text-yellow-300";
    case "degraded":   return "border-orange-400/40 bg-orange-400/10 text-orange-300";
    case "terminated": return "border-red-400/40 bg-red-400/10 text-red-300";
    default:           return "border-white/20 text-neutral-400";
  }
}

const SUB_TABS = [
  { segment: "console", label: "Console",  Icon: Terminal  },
  { segment: "cells",   label: "Cells",    Icon: Puzzle    },
  { segment: "memory",  label: "Memory",   Icon: Database  },
  { segment: "genome",  label: "Genome",   Icon: Brain     },
  { segment: "events",  label: "Events",   Icon: Activity  },
] as const;

export function OrganismNav({ id }: { id: string }) {
  const { detail, refresh } = useOrganismDetail();
  const { refresh: refreshList } = useOrganisms();
  const pathname = usePathname();
  const [busy, setBusy] = useState<string | null>(null);
  const organism = detail?.organism;

  async function handleWake() {
    setBusy("wake");
    try {
      await wakeOrganism(id);
      await Promise.all([refresh(), refreshList()]);
    } finally {
      setBusy(null);
    }
  }

  async function handleHibernate() {
    setBusy("hibernate");
    try {
      await hibernateOrganism(id);
      await Promise.all([refresh(), refreshList()]);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="border-b border-white/10">
      {/* Organism header */}
      <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-semibold text-white">
              {organism?.identity_profile.name ?? "Loading…"}
            </h1>
            {organism ? (
              <Badge variant="outline" className={lifecycleBadge(organism.lifecycle_state)}>
                {organism.lifecycle_state}
              </Badge>
            ) : null}
          </div>
          {organism ? (
            <p className="mt-0.5 text-sm text-neutral-400">
              {organism.identity_profile.purpose}
              <span className="ml-3 text-neutral-600">·</span>
              <span className="ml-3 text-neutral-500">stage: {organism.development_stage}</span>
              <span className="ml-3 text-neutral-600">·</span>
              <span className="ml-3 text-neutral-500">{detail?.cells.length ?? 0} cells</span>
            </p>
          ) : null}
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            className="border-white/15 text-neutral-300 hover:text-white"
            disabled={busy !== null}
            onClick={handleWake}
          >
            <Zap className="mr-1.5 size-3.5" />
            {busy === "wake" ? "Waking…" : "Wake"}
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="border-white/15 text-neutral-300 hover:text-white"
            disabled={busy !== null}
            onClick={handleHibernate}
          >
            <Moon className="mr-1.5 size-3.5" />
            {busy === "hibernate" ? "Hibernating…" : "Hibernate"}
          </Button>
        </div>
      </div>

      {/* Sub-navigation tabs */}
      <div className="flex items-center gap-0 px-6">
        {SUB_TABS.map(({ segment, label, Icon }) => {
          const href = `/organisms/${id}/${segment}`;
          const active = pathname.startsWith(href);
          return (
            <Link
              key={segment}
              href={href}
              className={`flex items-center gap-1.5 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
                active
                  ? "border-emerald-400 text-emerald-300"
                  : "border-transparent text-neutral-500 hover:text-neutral-200"
              }`}
            >
              <Icon className="size-3.5" />
              {label}
            </Link>
          );
        })}
      </div>
    </div>
  );
}
