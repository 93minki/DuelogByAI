"use client";

import { TurnCard } from "@/components/debate/turn-card";
import { roundLabel } from "@/lib/format";
import type { PartialTurn, RoundDecision, Source, Turn } from "@/lib/types";

interface TranscriptProps {
  turns: Turn[];
  sources: Map<number, Source>;
  partial?: PartialTurn | null;
  decisions?: RoundDecision[];
}

export function Transcript({ turns, sources, partial, decisions = [] }: TranscriptProps) {
  const groups = new Map<number, Turn[]>();
  for (const t of turns) {
    groups.set(t.round, [...(groups.get(t.round) ?? []), t]);
  }
  if (partial && !groups.has(partial.round)) groups.set(partial.round, []);
  const rounds = [...groups.keys()].sort((a, b) => a - b);

  return (
    <div className="space-y-8">
      {rounds.map((round) => {
        const decision = decisions.find((d) => d.round === round);
        return (
          <section key={round} className="space-y-4">
            <RoundDivider label={roundLabel(round)} />
            {groups.get(round)!.map((t) => (
              <TurnCard
                key={t.seq}
                speaker={t.speaker}
                phase={t.phase}
                content={t.content}
                sources={sources}
                searches={t.search_queries}
              />
            ))}
            {partial && partial.round === round && (
              <TurnCard
                speaker={partial.speaker}
                phase={partial.phase}
                content={partial.text}
                sources={sources}
                searches={partial.searches}
                live
              />
            )}
            {decision && (
              <p className="text-center text-xs text-muted-foreground">
                {decision.continue ? "사회자가 라운드 연장을 결정했습니다" : "사회자가 토론 라운드를 마치기로 했습니다"}
                {decision.reason ? ` — ${decision.reason}` : ""}
              </p>
            )}
          </section>
        );
      })}
    </div>
  );
}

function RoundDivider({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 text-xs font-semibold tracking-wide text-muted-foreground">
      <span className="h-px flex-1 bg-border" />
      {label}
      <span className="h-px flex-1 bg-border" />
    </div>
  );
}
