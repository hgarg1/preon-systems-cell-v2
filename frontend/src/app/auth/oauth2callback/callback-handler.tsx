"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { exchangeOAuthCode } from "@/lib/api";

export function OAuthCallbackHandler() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const attempted = useRef(false);

  useEffect(() => {
    if (attempted.current) return;
    attempted.current = true;

    const code = searchParams.get("code");
    const state = searchParams.get("state") ?? undefined;
    const errorParam = searchParams.get("error");

    if (errorParam) {
      setError(`Google declined sign-in: ${errorParam}`);
      return;
    }
    if (!code) {
      setError("No authorization code received from Google.");
      return;
    }

    exchangeOAuthCode("google", code, state)
      .then(() => {
        router.replace("/");
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Sign-in failed. Please try again.");
      });
  }, [router, searchParams]);

  if (error) {
    return (
      <div className="grid gap-4">
        <div className="rounded-lg border border-rose-300/20 bg-rose-950/50 px-4 py-3 text-sm text-rose-200">
          <p className="font-medium">Sign-in failed</p>
          <p className="mt-1 opacity-75">{error}</p>
        </div>
        <a href="/login" className="text-sm text-emerald-300 hover:underline">
          Back to sign in
        </a>
      </div>
    );
  }

  return (
    <div className="grid gap-4">
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full animate-pulse rounded-full bg-emerald-400/60"
          style={{ width: "100%" }}
        />
      </div>
      <p className="text-sm text-neutral-400">Completing sign-in with Google…</p>
    </div>
  );
}
