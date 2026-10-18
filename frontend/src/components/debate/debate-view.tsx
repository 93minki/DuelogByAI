"use client";

import { ArrowLeftIcon, Loader2Icon, SquareIcon } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";

import { DebateHeader } from "@/components/debate/debate-header";
import { SourceList } from "@/components/debate/source-list";
import { SummarySection } from "@/components/debate/summary-section";
import { Transcript } from "@/components/debate/transcript";
import { useDebateStream } from "@/components/debate/use-debate-stream";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { api, ApiError } from "@/lib/api";

export function DebateView({ debateId }: { debateId: string }) {
  const { debate, partial, decisions, connection } = useDebateStream(debateId);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [stopping, setStopping] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [follow, setFollow] = useState(true);

  const sourceMap = useMemo(() => new Map((debate?.sources ?? []).map((s) => [s.number, s])), [debate?.sources]);

  // 스트림을 열지 못했다면(404 등) 일반 요청으로 원인을 확인한다.
  useEffect(() => {
    if (connection !== "closed" || debate) return;
    api.getDebate(debateId).catch((err) => {
      setLoadError(err instanceof ApiError ? err.message : "토론을 불러오지 못했습니다.");
    });
  }, [connection, debate, debateId]);

  // 사용자가 맨 아래를 보고 있을 때만 새 발언을 따라 내려간다.
  useEffect(() => {
    const onScroll = () => {
      const nearBottom = window.innerHeight + window.scrollY >= document.body.scrollHeight - 200;
      setFollow(nearBottom);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  useEffect(() => {
    if (follow && debate?.status === "running") bottomRef.current?.scrollIntoView({ block: "end" });
  }, [partial?.text, debate?.turns.length, follow, debate?.status]);

  if (loadError) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 text-center">
        <p className="mb-4 text-muted-foreground">{loadError}</p>
        <Button asChild variant="outline">
          <Link href="/dashboard">대시보드로</Link>
        </Button>
      </div>
    );
  }

  if (!debate) {
    return (
      <div className="mx-auto max-w-4xl space-y-4 px-4 py-8">
        <Skeleton className="h-28 w-full" />
        <Skeleton className="h-40 w-[85%]" />
        <Skeleton className="ml-auto h-40 w-[85%]" />
      </div>
    );
  }

  const running = debate.status === "running";

  async function stop() {
    setStopping(true);
    try {
      await api.stopDebate(debateId);
      toast.success("토론을 종료했습니다.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "종료하지 못했습니다.");
    } finally {
      setStopping(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8 px-4 py-6 sm:py-8">
      <div className="flex items-center justify-between gap-2">
        <Button asChild variant="ghost" size="sm" className="-ml-2">
          <Link href="/dashboard">
            <ArrowLeftIcon /> 대시보드
          </Link>
        </Button>
        {running && (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" size="sm" disabled={stopping}>
                <SquareIcon /> 토론 종료
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>토론을 종료할까요?</AlertDialogTitle>
                <AlertDialogDescription>
                  지금까지의 발언은 저장되지만, 요약은 만들어지지 않습니다. 종료한 토론은 다시 이어갈 수 없습니다.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>계속 보기</AlertDialogCancel>
                <AlertDialogAction onClick={stop}>종료</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}
      </div>

      <DebateHeader debate={debate} />

      <Transcript turns={debate.turns} sources={sourceMap} partial={partial} decisions={decisions} />

      {running && !partial && (
        <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
          <Loader2Icon className="size-4 animate-spin" />
          {debate.turns.length === 0 ? "사회자가 논제를 정리하고 있습니다" : "다음 순서를 준비하고 있습니다"}
        </div>
      )}
      {running && connection === "connecting" && debate.turns.length > 0 && (
        <p className="text-center text-xs text-muted-foreground">연결이 끊겨 다시 연결하는 중입니다…</p>
      )}

      {debate.status === "stopped" && (
        <Notice>사용자가 토론을 종료했습니다. 종료 전까지의 발언만 저장되어 있으며 요약은 생성되지 않았습니다.</Notice>
      )}
      {debate.status === "failed" && <Notice tone="error">{debate.error ?? "토론 진행 중 오류가 발생했습니다."}</Notice>}

      {debate.summary && <SummarySection summary={debate.summary} sources={sourceMap} />}
      <SourceList sources={debate.sources} />
      <div ref={bottomRef} />
    </div>
  );
}

function Notice({ children, tone = "muted" }: { children: React.ReactNode; tone?: "muted" | "error" }) {
  return (
    <p
      className={
        tone === "error"
          ? "rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive"
          : "rounded-lg border bg-muted/50 p-4 text-sm text-muted-foreground"
      }
    >
      {children}
    </p>
  );
}
