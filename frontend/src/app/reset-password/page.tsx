import { AuthForm } from "@/components/auth/auth-form";
import { AuthShell } from "@/components/auth/auth-shell";
import { Suspense } from "react";

export default function ResetPasswordPage() {
  return (
    <AuthShell title="Set new password" subtitle="Use the reset token from the development stub response.">
      <Suspense fallback={null}>
        <AuthForm mode="reset" />
      </Suspense>
    </AuthShell>
  );
}
