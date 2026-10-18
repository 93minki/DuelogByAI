import { Suspense } from "react";

import { AuthForm } from "@/components/auth-form";

export const metadata = { title: "로그인 — 듀얼로그" };

export default function LoginPage() {
  return (
    <div className="flex justify-center px-4 py-16">
      <Suspense>
        <AuthForm mode="login" />
      </Suspense>
    </div>
  );
}
