import { Suspense } from "react";
import { AuthShell } from "@/components/auth/auth-shell";
import { OAuthCallbackHandler } from "./callback-handler";

export default function OAuthCallbackPage() {
  return (
    <AuthShell
      title="Completing sign-in"
      subtitle="Connecting your Google account to Preon…"
    >
      <Suspense fallback={null}>
        <OAuthCallbackHandler />
      </Suspense>
    </AuthShell>
  );
}
