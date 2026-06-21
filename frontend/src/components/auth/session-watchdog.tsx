"use client";

import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

const PUBLIC_PATHS = [
  "/",
  "/login",
  "/signup",
  "/forgot-password",
  "/reset-password",
  "/verify-email",
  "/auth",
];
const AUTO_ENTER_PATHS = [
  "/login",
  "/signup",
  "/forgot-password",
];

const SESSION_CHECK_INTERVAL_MS = 30_000;
const SESSION_ENDED_REDIRECT_DELAY_MS = 2_200;

export function SessionWatchdog() {
  const pathname = usePathname();
  const router = useRouter();
  const [sessionEnded, setSessionEnded] = useState(false);
  const redirectPending = useRef(false);

  const isPublicPath = PUBLIC_PATHS.some((path) => pathname === path || pathname.startsWith(`${path}/`));
  const shouldAutoEnter = AUTO_ENTER_PATHS.some((path) => pathname === path || pathname.startsWith(`${path}/`));

  const checkSession = useCallback(async () => {
    try {
      const response = await fetch("/backend/auth/me", {
        cache: "no-store",
        credentials: "include",
      });
      if (!isPublicPath && response.status === 401) {
        if (!redirectPending.current) {
          redirectPending.current = true;
          setSessionEnded(true);
          window.setTimeout(() => {
            router.replace(`/login?next=${encodeURIComponent(pathname)}`);
          }, SESSION_ENDED_REDIRECT_DELAY_MS);
        }
      } else if (shouldAutoEnter && response.ok) {
        const params = new URLSearchParams(window.location.search);
        router.replace(params.get("next") || "/");
      }
    } catch {
      // Network or backend availability errors should not force a logout.
    }
  }, [isPublicPath, pathname, router, shouldAutoEnter]);

  useEffect(() => {
    if (isPublicPath && !shouldAutoEnter) {
      return;
    }

    const intervalId = window.setInterval(() => {
      void checkSession();
    }, SESSION_CHECK_INTERVAL_MS);

    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        void checkSession();
      }
    };
    const handleFocus = () => {
      void checkSession();
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("focus", handleFocus);

    return () => {
      window.clearInterval(intervalId);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("focus", handleFocus);
    };
  }, [checkSession, isPublicPath, shouldAutoEnter]);

  if (!sessionEnded) return null;

  return (
    <div className="fixed inset-0 z-[200] flex items-start justify-center pt-6 pointer-events-none">
      <div className="pointer-events-auto mx-4 w-full max-w-sm rounded-lg border border-amber-300/30 bg-amber-950/95 px-5 py-4 shadow-2xl shadow-black/40 backdrop-blur">
        <p className="text-sm font-semibold text-amber-100">Session ended</p>
        <p className="mt-1 text-sm leading-5 text-amber-200/70">
          Your session ended — signing you out…
        </p>
      </div>
    </div>
  );
}
