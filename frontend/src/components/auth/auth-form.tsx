"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Mail, KeyRound, User, Circle, Building2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type React from "react";

import { useAuthToasts } from "@/components/auth/auth-toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  forgotPassword,
  getOAuthProvider,
  login,
  resetPassword,
  signup,
  verifyEmail,
} from "@/lib/api";

type Mode = "login" | "signup" | "forgot" | "reset" | "verify";

export function AuthForm({ mode }: { mode: Mode }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const tokenNoticeShown = useRef(false);
  const { pushToast, ToastViewport } = useAuthToasts();
  const token = searchParams.get("token") ?? "";
  const next = searchParams.get("next") || "/";

  useEffect(() => {
    if (tokenNoticeShown.current) return;
    if ((mode === "reset" || mode === "verify") && !token) {
      tokenNoticeShown.current = true;
      pushToast({
        tone: "error",
        title: mode === "reset" ? "Reset link is incomplete" : "Verification link is incomplete",
        description: "Open the link from the auth email stub or request a fresh one.",
      });
    }
  }, [mode, pushToast, token]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    try {
      if (mode === "signup") {
        const response = await signup({ email, password, name: name || undefined });
        pushToast({
          tone: "success",
          title: "Account created",
          description: response.email_verification_url
            ? `Dev — verification link: ${response.email_verification_url}`
            : "Check your email for a verification link.",
        });
        router.push(next);
      } else if (mode === "login") {
        await login({ email, password });
        pushToast({ tone: "success", title: "Signed in", description: "Your session is active across both dashboards." });
        router.push(next);
      } else if (mode === "forgot") {
        const response = await forgotPassword(email);
        pushToast({
          tone: "info",
          title: "Reset link sent",
          description: response.reset_url
            ? `Dev — reset link: ${response.reset_url}`
            : "If your email is registered, a reset link has been sent.",
        });
      } else if (mode === "reset") {
        await resetPassword({ token, password });
        pushToast({ tone: "success", title: "Password updated", description: "Sign in with the new password." });
        router.push("/login");
      } else if (mode === "verify") {
        await verifyEmail(token);
        pushToast({ tone: "success", title: "Email verified", description: "Your account verification state is updated." });
        router.push(next);
      }
      router.refresh();
    } catch (caught) {
      pushToast({
        tone: "error",
        title: mode === "login" ? "Sign in failed" : "Authentication failed",
        description: caught instanceof Error ? caught.message : "Authentication failed",
      });
    } finally {
      setBusy(false);
    }
  }

  async function handleOAuth(provider: "google" | "microsoft") {
    setBusy(true);
    try {
      const response = await getOAuthProvider(provider);
      if (response.configured && response.authorization_url) {
        window.location.href = response.authorization_url;
      } else {
        pushToast({
          tone: "info",
          title: "Provider not configured",
          description: `${provider} sign-on is not configured yet.`,
        });
      }
    } catch (caught) {
      pushToast({
        tone: "error",
        title: `${provider} sign-on failed`,
        description: caught instanceof Error ? caught.message : `${provider} sign-on failed`,
      });
    } finally {
      setBusy(false);
    }
  }

  const submitLabel = {
    login: "Sign in",
    signup: "Create account",
    forgot: "Prepare reset link",
    reset: "Update password",
    verify: "Verify email",
  }[mode];

  return (
    <form className="grid gap-4" onSubmit={handleSubmit}>
      <ToastViewport />
      {mode === "signup" ? (
        <Field label="Name" htmlFor="name" icon={User}>
          <Input id="name" autoComplete="name" value={name} onChange={(event) => setName(event.target.value)} className="h-11 border-white/10 bg-white/8 text-white placeholder:text-neutral-500" />
        </Field>
      ) : null}
      {mode === "login" || mode === "signup" || mode === "forgot" ? (
        <Field label="Email" htmlFor="email" icon={Mail}>
          <Input id="email" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} className="h-11 border-white/10 bg-white/8 text-white placeholder:text-neutral-500" />
        </Field>
      ) : null}
      {mode !== "forgot" && mode !== "verify" ? (
        <Field label="Password" htmlFor="password" icon={KeyRound}>
          <Input
            id="password"
            type="password"
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            required
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="h-11 border-white/10 bg-white/8 text-white placeholder:text-neutral-500"
          />
        </Field>
      ) : null}
      <Button disabled={busy || ((mode === "verify" || mode === "reset") && !token)} className="h-11 rounded-lg bg-emerald-300 font-semibold text-neutral-950 hover:bg-emerald-200">
        {busy ? "Working" : submitLabel}
      </Button>
      {mode === "login" || mode === "signup" ? (
        <div className="grid gap-2">
          <Button type="button" variant="outline" className="h-11 rounded-lg border-white/10 bg-white/5 text-white hover:bg-white/10" onClick={() => void handleOAuth("google")}>
            <Circle className="size-4" aria-hidden="true" />
            Continue with Google
          </Button>
          <Button type="button" variant="outline" className="h-11 rounded-lg border-white/10 bg-white/5 text-white hover:bg-white/10" onClick={() => void handleOAuth("microsoft")}>
            <Building2 className="size-4" aria-hidden="true" />
            Continue with Microsoft
          </Button>
        </div>
      ) : null}
      <AuthLinks mode={mode} />
    </form>
  );
}

function Field({
  label,
  htmlFor,
  icon: Icon,
  children,
}: {
  label: string;
  htmlFor: string;
  icon: typeof Mail;
  children: React.ReactNode;
}) {
  return (
    <div className="grid gap-2">
      <Label htmlFor={htmlFor} className="flex items-center gap-2 text-neutral-300">
        <Icon className="size-4 text-emerald-200" aria-hidden="true" />
        {label}
      </Label>
      {children}
    </div>
  );
}

function AuthLinks({ mode }: { mode: Mode }) {
  if (mode === "login") {
    return (
      <div className="flex items-center justify-between text-sm">
        <Link className="text-emerald-200 hover:underline" href="/signup">Create account</Link>
        <Link className="text-neutral-400 hover:text-white" href="/forgot-password">Forgot password?</Link>
      </div>
    );
  }
  return <Link className="text-sm text-emerald-200 hover:underline" href="/login">Back to sign in</Link>;
}
