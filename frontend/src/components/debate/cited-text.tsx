"use client";

import { Fragment } from "react";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { hostname } from "@/lib/format";
import type { Source } from "@/lib/types";

const CITATION = /\[(\d+)\]/g;

function renderInline(text: string, sources: Map<number, Source>, keyPrefix: string) {
  const parts: React.ReactNode[] = [];
  let last = 0;
  for (const match of text.matchAll(CITATION)) {
    const index = match.index ?? 0;
    if (index > last) parts.push(text.slice(last, index));
    const number = Number(match[1]);
    parts.push(<Citation key={`${keyPrefix}-${index}`} number={number} source={sources.get(number)} />);
    last = index + match[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

/** 본문을 문단/목록으로 나누고 [n]을 출처 툴팁으로 바꿔 렌더링한다. */
export function CitedText({ text, sources }: { text: string; sources: Map<number, Source> }) {
  const blocks = text.split(/\n{2,}/);
  return (
    <div className="space-y-3 leading-7">
      {blocks.map((block, bi) => {
        const lines = block.split("\n");
        const isList = lines.every((l) => /^\s*([-•*]|\d+\.)\s+/.test(l));
        if (isList) {
          return (
            <ul key={bi} className="list-disc space-y-1 pl-5">
              {lines.map((l, li) => (
                <li key={li}>{renderInline(l.replace(/^\s*([-•*]|\d+\.)\s+/, ""), sources, `${bi}-${li}`)}</li>
              ))}
            </ul>
          );
        }
        return (
          <p key={bi}>
            {lines.map((l, li) => (
              <Fragment key={li}>
                {li > 0 && <br />}
                {renderInline(l, sources, `${bi}-${li}`)}
              </Fragment>
            ))}
          </p>
        );
      })}
    </div>
  );
}

function Citation({ number, source }: { number: number; source?: Source }) {
  const label = (
    <a
      href={`#source-${number}`}
      className="mx-0.5 inline-flex h-4.5 min-w-4.5 -translate-y-1 items-center justify-center rounded bg-muted px-1 align-baseline text-[11px] font-semibold text-muted-foreground no-underline transition-colors hover:bg-foreground hover:text-background"
      aria-label={`출처 ${number}`}
    >
      {number}
    </a>
  );
  if (!source) return label;
  return (
    <Tooltip>
      <TooltipTrigger asChild>{label}</TooltipTrigger>
      <TooltipContent className="max-w-xs">
        <p className="font-medium">{source.title}</p>
        <p className="opacity-70">
          {hostname(source.url)}
          {source.published_date ? ` · ${source.published_date.slice(0, 10)}` : ""}
        </p>
      </TooltipContent>
    </Tooltip>
  );
}
