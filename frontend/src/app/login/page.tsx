import { AuthForm } from "@/components/auth/auth-form";
import { AuthShell } from "@/components/auth/auth-shell";
import { Suspense } from "react";

export default function LoginPage() {
  return (
    <AuthShell title="Sign in" subtitle="Use your Preon account to unlock organisms, signals, contracts, and the FastAPI console.">
      <Suspense fallback={null}>
        <AuthForm mode="login" />
      </Suspense>
    </AuthShell>
  );
}
