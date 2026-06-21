import { AuthForm } from "@/components/auth/auth-form";
import { AuthShell } from "@/components/auth/auth-shell";
import { Suspense } from "react";

export default function VerifyEmailPage() {
  return (
    <AuthShell title="Verify email" subtitle="Complete the local verification stub for this account.">
      <Suspense fallback={null}>
        <AuthForm mode="verify" />
      </Suspense>
    </AuthShell>
  );
}
