import { Suspense } from "react";

import { AuthForm } from "@/components/auth-form";

export const metadata = { title: "회원가입 — 듀얼로그" };

export default function SignupPage() {
  return (
    <div className="flex justify-center px-4 py-16">
      <Suspense>
        <AuthForm mode="signup" />
      </Suspense>
    </div>
  );
}
