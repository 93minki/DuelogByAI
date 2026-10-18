"use client";

import { useEffect, useState } from "react";

import { DebateList } from "@/components/dashboard/debate-list";
import { NewDebateForm } from "@/components/dashboard/new-debate-form";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api, ApiError } from "@/lib/api";
import type { DebateListItem } from "@/lib/types";

export default function DashboardPage() {
  const [debates, setDebates] = useState<DebateListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listDebates()
      .then(setDebates)
      .catch((err) => setError(err instanceof ApiError ? err.message : "목록을 불러오지 못했습니다."));
  }, []);

  const running = debates?.some((d) => d.status === "running");

  return (
    <div className="mx-auto max-w-3xl space-y-8 px-4 py-8">
      <Card>
        <CardHeader>
          <CardTitle className="text-xl">새 토론 시작</CardTitle>
          <CardDescription>
            찬반이 갈리는 주제를 입력하면 사회자·찬성·반대 AI가 웹 검색 근거로 토론합니다.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <NewDebateForm
            disabledReason={running ? "진행 중인 토론이 끝나거나 종료한 뒤 새 토론을 시작할 수 있습니다." : null}
          />
        </CardContent>
      </Card>

      <section className="space-y-3">
        <h2 className="text-lg font-bold">내 토론</h2>
        {error && <p className="text-sm text-destructive">{error}</p>}
        {!debates && !error && (
          <div className="grid gap-3">
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
          </div>
        )}
        {debates && (
          <DebateList debates={debates} onDeleted={(id) => setDebates((ds) => ds?.filter((d) => d.id !== id) ?? null)} />
        )}
      </section>
    </div>
  );
}
