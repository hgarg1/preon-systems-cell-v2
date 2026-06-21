"use client";

import { CircleAlert, CircleCheck, Info, X } from "lucide-react";
import { useCallback, useState } from "react";

type ToastTone = "success" | "error" | "info";

type AuthToast = {
  id: number;
  tone: ToastTone;
  title: string;
  description?: string;
};

const icons = {
  success: CircleCheck,
  error: CircleAlert,
  info: Info,
};

const toneClass = {
  success: "border-emerald-300/30 bg-emerald-950/95 text-emerald-50",
  error: "border-rose-300/30 bg-rose-950/95 text-rose-50",
  info: "border-sky-300/30 bg-sky-950/95 text-sky-50",
};

export function useAuthToasts() {
  const [toasts, setToasts] = useState<AuthToast[]>([]);

  const dismissToast = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const pushToast = useCallback((toast: Omit<AuthToast, "id">) => {
    const id = Date.now() + Math.floor(Math.random() * 1000);
    setToasts((current) => [...current.slice(-2), { ...toast, id }]);
    window.setTimeout(() => dismissToast(id), 5600);
    return id;
  }, [dismissToast]);

  function ToastViewport() {
    return (
      <div className="pointer-events-none fixed inset-x-4 top-4 z-50 grid gap-3 sm:left-auto sm:right-5 sm:w-[24rem]">
        {toasts.map((toast) => {
          const Icon = icons[toast.tone];
          return (
            <div
              key={toast.id}
              className={`pointer-events-auto rounded-lg border p-4 shadow-2xl shadow-black/30 backdrop-blur ${toneClass[toast.tone]}`}
              role={toast.tone === "error" ? "alert" : "status"}
            >
              <div className="flex gap-3">
                <Icon className="mt-0.5 size-5 shrink-0" aria-hidden="true" />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold">{toast.title}</p>
                  {toast.description ? (
                    <p className="mt-1 break-words text-sm leading-5 opacity-85">{toast.description}</p>
                  ) : null}
                </div>
                <button
                  type="button"
                  className="grid size-7 shrink-0 place-items-center rounded-md text-white/70 transition hover:bg-white/10 hover:text-white"
                  onClick={() => dismissToast(toast.id)}
                  aria-label="Dismiss notification"
                >
                  <X className="size-4" aria-hidden="true" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  return { pushToast, ToastViewport };
}
