"use client";

import { useMemo } from "react";

import { DebateHeader } from "@/components/debate/debate-header";
import { SourceList } from "@/components/debate/source-list";
import { SummarySection } from "@/components/debate/summary-section";
import { Transcript } from "@/components/debate/transcript";
import { SAMPLE_DEBATE } from "@/lib/sample-debate";

export function SamplePreview() {
  const d = SAMPLE_DEBATE;
  const sources = useMemo(() => new Map(d.sources.map((s) => [s.number, s])), [d.sources]);
  return (
    <div className="space-y-8 rounded-3xl border bg-background p-4 shadow-sm sm:p-8">
      <DebateHeader debate={d} />
      <Transcript turns={d.turns} sources={sources} />
      {d.summary && <SummarySection summary={d.summary} sources={sources} />}
      <SourceList sources={d.sources} />
    </div>
  );
}
