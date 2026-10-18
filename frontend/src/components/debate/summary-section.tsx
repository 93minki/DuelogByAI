"use client";

import { CitedText } from "@/components/debate/cited-text";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { Source, Summary } from "@/lib/types";

export function SummarySection({ summary, sources }: { summary: Summary; sources: Map<number, Source> }) {
  const f = summary.final_summary;
  return (
    <section aria-labelledby="summary-title" className="space-y-4">
      <h2 id="summary-title" className="text-lg font-bold">
        토론 요약
      </h2>
      <div className="grid gap-4 md:grid-cols-2">
        <SideSummary title="찬성 측 요약" tone="pro" text={summary.pro_summary} sources={sources} />
        <SideSummary title="반대 측 요약" tone="con" text={summary.con_summary} sources={sources} />
      </div>
      <Card>
        <CardHeader>
          <CardTitle>최종 요약</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5 text-[15px]">
          <p className="leading-7">{f.overview}</p>
          <div className="grid gap-5 sm:grid-cols-2">
            <SummaryList title="핵심 쟁점" items={f.key_issues} />
            <SummaryList title="끝까지 대립한 부분" items={f.disagreements} />
            <SummaryList title="양측이 공통으로 인정한 부분" items={f.agreements} empty="뚜렷한 합의점은 없었습니다." />
            <SummaryList title="더 생각해 볼 질문" items={f.open_questions} />
          </div>
          <p className="border-t pt-4 text-xs text-muted-foreground">
            듀얼로그는 승패나 설득력을 판정하지 않습니다. 어느 쪽 주장이 더 타당한지는 출처를 확인하며 직접 판단해 주세요.
          </p>
        </CardContent>
      </Card>
    </section>
  );
}

function SideSummary({
  title,
  tone,
  text,
  sources,
}: {
  title: string;
  tone: "pro" | "con";
  text: string;
  sources: Map<number, Source>;
}) {
  return (
    <Card className={cn("border-t-4", tone === "pro" ? "border-t-pro" : "border-t-con")}>
      <CardHeader>
        <CardTitle className={tone === "pro" ? "text-pro" : "text-con"}>{title}</CardTitle>
      </CardHeader>
      <CardContent className="text-[15px]">
        <CitedText text={text} sources={sources} />
      </CardContent>
    </Card>
  );
}

function SummaryList({ title, items, empty }: { title: string; items: string[]; empty?: string }) {
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold">{title}</h3>
      {items.length > 0 ? (
        <ul className="list-disc space-y-1 pl-5 text-sm leading-6">
          {items.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">{empty ?? "없음"}</p>
      )}
    </div>
  );
}
