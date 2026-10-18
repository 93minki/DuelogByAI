"use client";

import { GavelIcon, SearchIcon, ThumbsDownIcon, ThumbsUpIcon } from "lucide-react";

import { CitedText } from "@/components/debate/cited-text";
import { cn } from "@/lib/utils";
import { PHASE_LABEL, SPEAKER_LABEL } from "@/lib/format";
import type { Phase, Source, Speaker } from "@/lib/types";

const STYLE: Record<Speaker, { wrap: string; card: string; badge: string; icon: React.ElementType }> = {
  moderator: {
    wrap: "md:mx-auto md:w-[85%]",
    card: "bg-moderator-soft border-border",
    badge: "bg-moderator text-background",
    icon: GavelIcon,
  },
  pro: {
    wrap: "md:mr-auto md:w-[88%]",
    card: "bg-card border-l-4 border-l-pro",
    badge: "bg-pro text-white dark:text-background",
    icon: ThumbsUpIcon,
  },
  con: {
    wrap: "md:ml-auto md:w-[88%]",
    card: "bg-card border-r-4 border-r-con",
    badge: "bg-con text-white dark:text-background",
    icon: ThumbsDownIcon,
  },
};

interface TurnCardProps {
  speaker: Speaker;
  phase: Phase;
  content: string;
  sources: Map<number, Source>;
  searches?: string[];
  live?: boolean;
}

export function TurnCard({ speaker, phase, content, sources, searches = [], live = false }: TurnCardProps) {
  const style = STYLE[speaker];
  const Icon = style.icon;
  return (
    <article className={cn("w-full", style.wrap)}>
      <div className={cn("rounded-xl border p-4 shadow-xs sm:p-5", style.card)}>
        <header className="mb-3 flex flex-wrap items-center gap-2">
          <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold", style.badge)}>
            <Icon className="size-3.5" />
            {SPEAKER_LABEL[speaker]}
          </span>
          <span className="text-xs text-muted-foreground">{PHASE_LABEL[phase]}</span>
          {searches.length > 0 && (
            <span className="ml-auto text-xs text-muted-foreground">검색 {searches.length}회</span>
          )}
        </header>

        {live && searches.length > 0 && !content && (
          <ul className="mb-2 space-y-1 text-sm text-muted-foreground">
            {searches.map((q, i) => (
              <li key={i} className="flex items-center gap-2">
                <SearchIcon className={cn("size-3.5 shrink-0", i === searches.length - 1 && "animate-pulse")} />
                <span className="truncate">‘{q}’ 검색{i === searches.length - 1 ? " 중…" : " 완료"}</span>
              </li>
            ))}
          </ul>
        )}

        {content ? (
          <div className={cn("text-[15px]", live && "typing-caret")}>
            <CitedText text={content} sources={sources} />
          </div>
        ) : (
          live &&
          searches.length === 0 && <p className="typing-caret text-sm text-muted-foreground">생각을 정리하는 중</p>
        )}
      </div>
    </article>
  );
}
