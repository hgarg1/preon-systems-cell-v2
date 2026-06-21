import Link from "next/link";
import { Atom, Database, KeyRound, ShieldCheck } from "lucide-react";
import type React from "react";

export function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_15%_10%,rgba(79,230,164,0.18),transparent_28rem),radial-gradient(circle_at_90%_90%,rgba(96,165,250,0.16),transparent_26rem),linear-gradient(135deg,#05070a,#111827_58%,#07111f)] px-5 py-8 text-foreground">
      <div className="mx-auto grid min-h-[calc(100vh-4rem)] w-full max-w-6xl items-center gap-8 lg:grid-cols-[1fr_27rem]">
        <section className="max-w-3xl">
          <Link href="/" className="mb-8 inline-flex items-center gap-3 text-emerald-100">
            <span className="grid size-10 place-items-center rounded-lg border border-emerald-300/25 bg-emerald-300/12">
              <Atom className="size-5" aria-hidden="true" />
            </span>
            <span>
              <span className="block text-sm font-medium">Preon Systems</span>
              <span className="block font-mono text-xs text-neutral-400">Organism runtime control plane</span>
            </span>
          </Link>
          <h1 className="text-4xl font-semibold leading-tight text-white sm:text-5xl">
            Secure organism operations for admitted signals.
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-neutral-300">
            Session access covers organisms, signals, contracts, and runtime events with the same private boundary.
          </p>
          <div className="mt-8 grid max-w-xl gap-3 sm:grid-cols-3">
            <TrustPill icon={ShieldCheck} label="HttpOnly session" />
            <TrustPill icon={Database} label="Private organisms" />
            <TrustPill icon={KeyRound} label="Guarded contracts" />
          </div>
        </section>
        <section className="relative overflow-hidden rounded-lg border border-white/10 bg-neutral-950/88 p-6 shadow-2xl shadow-black/30">
          <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-emerald-300 via-sky-300 to-emerald-300" />
          <div className="mb-6">
            <h2 className="text-2xl font-semibold text-white">{title}</h2>
            <p className="mt-2 text-sm leading-6 text-neutral-400">{subtitle}</p>
          </div>
          {children}
          {footer ? <div className="mt-6 border-t border-white/10 pt-5 text-sm text-neutral-400">{footer}</div> : null}
        </section>
      </div>
    </main>
  );
}

function TrustPill({ icon: Icon, label }: { icon: typeof ShieldCheck; label: string }) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-white/10 bg-neutral-950/65 px-3 py-2 text-sm text-neutral-200">
      <Icon className="size-4 text-emerald-200" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
