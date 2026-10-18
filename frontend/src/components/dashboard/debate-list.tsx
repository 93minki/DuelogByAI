"use client";

import { MessagesSquareIcon, Trash2Icon } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

import { StatusBadge } from "@/components/status-badge";
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
import { api, ApiError } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { DebateListItem } from "@/lib/types";
import { cn } from "@/lib/utils";

export function DebateList({ debates, onDeleted }: { debates: DebateListItem[]; onDeleted: (id: string) => void }) {
  if (debates.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed p-10 text-center text-muted-foreground">
        <MessagesSquareIcon className="size-8 opacity-50" />
        <p>아직 진행한 토론이 없습니다. 위에서 첫 주제를 입력해 보세요.</p>
      </div>
    );
  }

  return (
    <ul className="grid gap-3">
      {debates.map((d) => (
        <li key={d.id}>
          <div
            className={cn(
              "group relative flex items-start gap-3 rounded-xl border bg-card p-4 transition-colors hover:bg-accent/50",
              d.status === "running" && "border-emerald-500/50",
            )}
          >
            <Link href={`/debates/${d.id}`} className="min-w-0 flex-1 after:absolute after:inset-0">
              <div className="mb-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                <StatusBadge status={d.status} />
                <span>{formatDate(d.created_at)}</span>
                {d.total_rounds && <span>· {d.total_rounds}라운드</span>}
                {d.status === "running" && <span className="font-medium text-emerald-600 dark:text-emerald-400">이어 보기 →</span>}
              </div>
              <p className="font-medium leading-snug">{d.proposition ?? d.topic_raw}</p>
              {d.proposition && d.proposition !== d.topic_raw && (
                <p className="mt-0.5 truncate text-xs text-muted-foreground">입력: {d.topic_raw}</p>
              )}
            </Link>
            <DeleteButton debate={d} onDeleted={onDeleted} />
          </div>
        </li>
      ))}
    </ul>
  );
}

function DeleteButton({ debate, onDeleted }: { debate: DebateListItem; onDeleted: (id: string) => void }) {
  async function remove() {
    try {
      await api.deleteDebate(debate.id);
      onDeleted(debate.id);
      toast.success("토론을 삭제했습니다.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "삭제하지 못했습니다.");
    }
  }
  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="ghost" size="icon" className="relative z-10 shrink-0 text-muted-foreground" aria-label="삭제">
          <Trash2Icon />
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>토론을 삭제할까요?</AlertDialogTitle>
          <AlertDialogDescription>
            발언, 출처, 요약이 모두 영구 삭제되며 되돌릴 수 없습니다.
            {debate.status === "running" && " 진행 중인 토론은 종료한 뒤 삭제합니다."}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>취소</AlertDialogCancel>
          <AlertDialogAction onClick={remove} className="bg-destructive text-white hover:bg-destructive/90">
            삭제
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
