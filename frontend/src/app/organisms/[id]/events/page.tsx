"use client";

import { Badge } from "@/components/ui/badge";
import { useOrganismDetail } from "@/lib/organism-detail-context";

const ORGANELLE_STYLES: Record<string, { border: string; bg: string; badge: string }> = {
  membrane:         { border: "border-cyan-400/30",    bg: "bg-cyan-400/5",    badge: "border-cyan-400/40 text-cyan-300" },
  nucleus:          { border: "border-violet-400/30",  bg: "bg-violet-400/5",  badge: "border-violet-400/40 text-violet-300" },
  mitochondria:     { border: "border-amber-400/30",   bg: "bg-amber-400/5",   badge: "border-amber-400/40 text-amber-300" },
  ribosome:         { border: "border-emerald-400/30", bg: "bg-emerald-400/5", badge: "border-emerald-400/40 text-emerald-300" },
  protein:          { border: "border-purple-400/30",  bg: "bg-purple-400/5",  badge: "border-purple-400/40 text-purple-300" },
  golgi:            { border: "border-orange-400/30",  bg: "bg-orange-400/5",  badge: "border-orange-400/40 text-orange-300" },
  skeleton:         { border: "border-pink-400/30",    bg: "bg-pink-400/5",    badge: "border-pink-400/40 text-pink-300" },
  structure_request:{ border: "border-pink-400/30",    bg: "bg-pink-400/5",    badge: "border-pink-400/40 text-pink-300" },
  peroxisome:       { border: "border-red-400/30",     bg: "bg-red-400/5",     badge: "border-red-400/40 text-red-300" },
};

const DEFAULT_STYLE = { border: "border-white/10", bg: "bg-neutral-950", badge: "border-white/20 text-neutral-400" };

export default function EventsPage() {
  const { detail, loading } = useOrganismDetail();

  if (loading) return <div className="p-6 text-sm text-neutral-500">Loading events…</div>;

  const events = [...(detail?.events ?? [])].reverse();

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-white">Events</h2>
          <p className="mt-0.5 text-sm text-neutral-500">
            Organelle-tagged runtime trace for this organism. Most recent first.
          </p>
        </div>
        <span className="text-xs text-neutral-600">{events.length} events</span>
      </div>

      {events.length === 0 ? (
        <div className="rounded-lg border border-dashed border-white/10 py-16 text-center">
          <p className="text-sm text-neutral-600">No events recorded yet</p>
          <p className="mt-1 text-xs text-neutral-700">Submit a signal from the Console to generate events</p>
        </div>
      ) : (
        <div className="space-y-2">
          {events.map((event) => {
            const style = ORGANELLE_STYLES[event.type] ?? DEFAULT_STYLE;
            return (
              <div key={event.event_id} className={`rounded-lg border p-3 ${style.border} ${style.bg}`}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <Badge variant="outline" className={`text-xs ${style.badge}`}>
                    {event.type}
                  </Badge>
                  <span className="font-mono text-xs text-neutral-600">
                    {new Date(event.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="mt-2 text-sm text-neutral-200">{event.message}</p>
                {Object.keys(event.values).length > 0 ? (
                  <details className="mt-2">
                    <summary className="cursor-pointer text-[10px] text-neutral-600 hover:text-neutral-400">values</summary>
                    <pre className="mt-1 max-h-32 overflow-auto rounded bg-black/30 p-2 text-[10px] text-neutral-400">
                      {JSON.stringify(event.values, null, 2)}
                    </pre>
                  </details>
                ) : null}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
