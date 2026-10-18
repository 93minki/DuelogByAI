import { StatusBadge } from "@/components/status-badge";
import { roundLabel } from "@/lib/format";
import type { DebateDetail } from "@/lib/types";

type HeaderDebate = Pick<
  DebateDetail,
  "topic_raw" | "proposition" | "pro_stance" | "con_stance" | "status" | "current_round" | "total_rounds"
>;

export function DebateHeader({ debate }: { debate: HeaderDebate }) {
  const roundInfo =
    debate.status === "running" && debate.current_round > 0
      ? `${roundLabel(debate.current_round)} 진행 중`
      : debate.total_rounds
        ? `총 ${debate.total_rounds}라운드`
        : null;

  return (
    <header className="space-y-4 rounded-2xl border bg-card p-5 sm:p-6">
      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <StatusBadge status={debate.status} />
        {roundInfo && <span>{roundInfo}</span>}
        <span className="truncate">입력한 주제: {debate.topic_raw}</span>
      </div>
      <h1 className="text-xl font-bold leading-snug sm:text-2xl">
        {debate.proposition ?? <span className="text-muted-foreground">논제를 정리하는 중…</span>}
      </h1>
      {debate.pro_stance && debate.con_stance && (
        <div className="grid gap-3 sm:grid-cols-2">
          <Stance tone="pro" label="찬성" text={debate.pro_stance} />
          <Stance tone="con" label="반대" text={debate.con_stance} />
        </div>
      )}
    </header>
  );
}

function Stance({ tone, label, text }: { tone: "pro" | "con"; label: string; text: string }) {
  return (
    <div className={tone === "pro" ? "rounded-lg bg-pro-soft p-3" : "rounded-lg bg-con-soft p-3"}>
      <p className={tone === "pro" ? "mb-1 text-xs font-semibold text-pro" : "mb-1 text-xs font-semibold text-con"}>
        {label}
      </p>
      <p className="text-sm leading-6">{text}</p>
    </div>
  );
}
