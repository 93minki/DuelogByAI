"use client";

import { AlertCircleIcon, Loader2Icon, SparklesIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { api, ApiError, topicVerdictFrom, type TopicVerdictDetail } from "@/lib/api";
import { cn } from "@/lib/utils";

const MIN = 2;
const MAX = 200;
const EXAMPLES = ["대형마트 의무휴업을 폐지해야 한다", "기본소득 도입", "초등학교 수업 중 스마트폰 사용을 금지해야 한다"];

export function NewDebateForm({ disabledReason }: { disabledReason?: string | null }) {
  const router = useRouter();
  const [topic, setTopic] = useState("");
  const [pending, setPending] = useState(false);
  const [verdict, setVerdict] = useState<TopicVerdictDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const length = topic.trim().length;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setVerdict(null);
    setError(null);
    setPending(true);
    try {
      const debate = await api.createDebate(topic);
      router.push(`/debates/${debate.id}`);
    } catch (err) {
      const v = topicVerdictFrom(err);
      if (v) setVerdict(v);
      else setError(err instanceof ApiError ? err.message : "네트워크 오류가 발생했습니다.");
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <Textarea
        value={topic}
        onChange={(e) => {
          setTopic(e.target.value);
          setVerdict(null);
        }}
        placeholder="토론할 주제를 입력하세요. 예: 대형마트 의무휴업을 폐지해야 한다"
        maxLength={MAX}
        rows={3}
        className="resize-none text-base"
        disabled={pending}
        aria-invalid={verdict ? true : undefined}
      />
      <div className="flex flex-wrap items-center gap-2">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            type="button"
            onClick={() => setTopic(ex)}
            className="rounded-full border px-3 py-1 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          >
            {ex}
          </button>
        ))}
      </div>

      {verdict && (
        <div
          role="alert"
          className={cn(
            "flex gap-2 rounded-lg border p-3 text-sm",
            verdict.status === "rejected"
              ? "border-destructive/40 bg-destructive/5 text-destructive"
              : "border-amber-500/40 bg-amber-500/5 text-amber-700 dark:text-amber-400",
          )}
        >
          <AlertCircleIcon className="mt-0.5 size-4 shrink-0" />
          <p>{verdict.message}</p>
        </div>
      )}
      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}

      <div className="flex items-center justify-between gap-3">
        <span className="text-xs text-muted-foreground">
          {length}/{MAX}자 · 입력한 주제는 토론 가능 여부를 먼저 판정합니다
        </span>
        <Button type="submit" disabled={pending || length < MIN || !!disabledReason} title={disabledReason ?? undefined}>
          {pending ? <Loader2Icon className="animate-spin" /> : <SparklesIcon />}
          {pending ? "주제 확인 중…" : "토론 시작"}
        </Button>
      </div>
      {disabledReason && <p className="text-right text-xs text-muted-foreground">{disabledReason}</p>}
    </form>
  );
}
