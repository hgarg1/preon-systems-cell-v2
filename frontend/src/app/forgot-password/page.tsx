import { AuthForm } from "@/components/auth/auth-form";
import { AuthShell } from "@/components/auth/auth-shell";
import { Suspense } from "react";

export default function ForgotPasswordPage() {
  return (
    <AuthShell title="Reset access" subtitle="Generate a password reset token for local development.">
      <Suspense fallback={null}>
        <AuthForm mode="forgot" />
      </Suspense>
    </AuthShell>
  );
}
