"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api, ApiError } from "@/lib/api";

const PASSWORD_MIN = 8;

export function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const router = useRouter();
  const params = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const isSignup = mode === "signup";

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (isSignup && password.length < PASSWORD_MIN) {
      setError(`비밀번호는 ${PASSWORD_MIN}자 이상이어야 합니다.`);
      return;
    }
    if (isSignup && password !== confirm) {
      setError("비밀번호가 일치하지 않습니다.");
      return;
    }
    setPending(true);
    try {
      await (isSignup ? api.signup(email, password) : api.login(email, password));
      const next = params.get("next");
      router.push(next && next.startsWith("/") && !next.startsWith("//") ? next : "/dashboard");
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "네트워크 오류가 발생했습니다.");
      setPending(false);
    }
  }

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle className="text-xl">{isSignup ? "회원가입" : "로그인"}</CardTitle>
        <CardDescription>
          {isSignup ? "이메일과 비밀번호만으로 시작할 수 있습니다." : "듀얼로그에 오신 것을 환영합니다."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <div className="grid gap-2">
            <Label htmlFor="email">이메일</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="password">비밀번호</Label>
            <Input
              id="password"
              type="password"
              autoComplete={isSignup ? "new-password" : "current-password"}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            {isSignup && <p className="text-xs text-muted-foreground">{PASSWORD_MIN}자 이상</p>}
          </div>
          {isSignup && (
            <div className="grid gap-2">
              <Label htmlFor="confirm">비밀번호 확인</Label>
              <Input
                id="confirm"
                type="password"
                autoComplete="new-password"
                required
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
              />
            </div>
          )}
          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}
          <Button type="submit" disabled={pending}>
            {pending ? "처리 중…" : isSignup ? "가입하기" : "로그인"}
          </Button>
          <p className="text-center text-sm text-muted-foreground">
            {isSignup ? "이미 계정이 있나요? " : "처음이신가요? "}
            <Link href={isSignup ? "/login" : "/signup"} className="font-medium text-foreground underline-offset-4 hover:underline">
              {isSignup ? "로그인" : "회원가입"}
            </Link>
          </p>
        </form>
      </CardContent>
    </Card>
  );
}
