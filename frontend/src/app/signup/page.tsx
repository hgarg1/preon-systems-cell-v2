import { AuthForm } from "@/components/auth/auth-form";
import { AuthShell } from "@/components/auth/auth-shell";
import { Suspense } from "react";

export default function SignupPage() {
  return (
    <AuthShell title="Create account" subtitle="New accounts receive a stub verification link until email delivery is wired.">
      <Suspense fallback={null}>
        <AuthForm mode="signup" />
      </Suspense>
    </AuthShell>
  );
}
