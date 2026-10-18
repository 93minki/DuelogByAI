import { ExternalLinkIcon } from "lucide-react";

import { hostname } from "@/lib/format";
import type { Source } from "@/lib/types";

export function SourceList({ sources }: { sources: Source[] }) {
  if (sources.length === 0) return null;
  return (
    <section aria-labelledby="sources-title" className="space-y-3">
      <h2 id="sources-title" className="text-lg font-bold">
        출처 <span className="text-sm font-normal text-muted-foreground">{sources.length}건</span>
      </h2>
      <ol className="divide-y rounded-xl border bg-card">
        {sources.map((s) => (
          <li key={s.number} id={`source-${s.number}`} className="flex scroll-mt-24 gap-3 p-3 target:bg-accent">
            <span className="mt-0.5 inline-flex h-5 min-w-5 items-center justify-center rounded bg-muted px-1 text-xs font-semibold text-muted-foreground">
              {s.number}
            </span>
            <div className="min-w-0 flex-1">
              <a
                href={s.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex max-w-full items-center gap-1 font-medium hover:underline"
              >
                <span className="truncate">{s.title}</span>
                <ExternalLinkIcon className="size-3.5 shrink-0 opacity-60" />
              </a>
              <p className="text-xs text-muted-foreground">
                {hostname(s.url)}
                {s.published_date ? ` · ${s.published_date.slice(0, 10)}` : ""}
                {s.author ? ` · ${s.author}` : ""}
              </p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
