import { FileSearchIcon, GavelIcon, ListChecksIcon, ScaleIcon, ShieldCheckIcon, SparklesIcon } from "lucide-react";
import { cookies } from "next/headers";
import Link from "next/link";

import { SamplePreview } from "@/components/landing/sample-preview";
import { Button } from "@/components/ui/button";
import { AUTH_COOKIE } from "@/lib/auth-cookie";

const STEPS = [
  {
    icon: ShieldCheckIcon,
    title: "주제 입력과 판정",
    body: "입력한 주제가 토론 가능한지 결정 모델(JEV)이 먼저 판정합니다. 사실 질문이나 유해한 주제는 걸러 냅니다.",
  },
  {
    icon: FileSearchIcon,
    title: "근거 기반 토론",
    body: "사회자의 진행에 따라 찬성·반대 AI가 매 발언마다 웹을 검색해 근거를 찾고, 출처 번호를 붙여 주장합니다.",
  },
  {
    icon: ListChecksIcon,
    title: "중립 요약",
    body: "토론이 끝나면 찬성 요약, 반대 요약, 핵심 쟁점과 대립점을 정리한 최종 요약을 제공합니다.",
  },
];

const FEATURES = [
  { icon: SparklesIcon, title: "실시간 진행", body: "발언이 작성되는 과정과 검색어를 그대로 지켜볼 수 있습니다." },
  { icon: GavelIcon, title: "중립 사회자", body: "사회자는 쟁점을 정리하고 다음 논점을 던질 뿐, 판정하지 않습니다." },
  { icon: ScaleIcon, title: "판단은 사용자 몫", body: "승패나 설득력 평가는 없습니다. 출처를 확인하며 직접 판단하세요." },
];

export default async function LandingPage() {
  const loggedIn = (await cookies()).has(AUTH_COOKIE);
  const cta = loggedIn ? { href: "/dashboard", label: "대시보드로 가기" } : { href: "/signup", label: "무료로 시작하기" };

  return (
    <div>
      <section className="relative overflow-hidden border-b">
        <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute -left-32 top-10 size-96 rounded-full bg-pro/15 blur-3xl" />
          <div className="absolute -right-32 bottom-0 size-96 rounded-full bg-con/15 blur-3xl" />
        </div>
        <div className="mx-auto max-w-4xl px-4 py-20 text-center sm:py-28">
          <p className="mb-4 text-sm font-medium text-muted-foreground">사회자 · 찬성 · 반대, 세 AI의 토론</p>
          <h1 className="text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
            주장에는 <span className="text-pro">근거</span>를,
            <br />
            근거에는 <span className="text-con">출처</span>를.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-muted-foreground">
            듀얼로그는 찬반이 갈리는 주제를 AI들이 웹 검색 자료로 토론하게 하고, 모든 주장에 출처를 붙여 보여줍니다.
            결론은 당신이 내리세요.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Button asChild size="lg">
              <Link href={cta.href}>{cta.label}</Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <a href="#sample">토론 예시 보기</a>
            </Button>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16">
        <h2 className="mb-8 text-center text-2xl font-bold">이렇게 진행됩니다</h2>
        <ol className="grid gap-4 md:grid-cols-3">
          {STEPS.map((s, i) => (
            <li key={s.title} className="rounded-2xl border bg-card p-6">
              <div className="mb-4 flex items-center gap-3">
                <span className="inline-flex size-9 items-center justify-center rounded-full bg-secondary">
                  <s.icon className="size-4" />
                </span>
                <span className="text-sm font-semibold text-muted-foreground">STEP {i + 1}</span>
              </div>
              <h3 className="mb-2 font-bold">{s.title}</h3>
              <p className="text-sm leading-6 text-muted-foreground">{s.body}</p>
            </li>
          ))}
        </ol>
        <p className="mt-6 text-center text-sm text-muted-foreground">
          기본 3라운드로 진행되며, 다룰 논점이 남아 있으면 사회자가 최대 5라운드까지 연장합니다.
        </p>
      </section>

      <section id="sample" className="scroll-mt-16 border-y bg-muted/40">
        <div className="mx-auto max-w-4xl px-4 py-16">
          <div className="mb-8 text-center">
            <h2 className="text-2xl font-bold">토론 예시</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              실제 토론 화면을 축약한 예시입니다. 실제 토론은 3~5라운드와 최종 발언으로 이어집니다.
            </p>
          </div>
          <SamplePreview />
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16">
        <div className="grid gap-4 md:grid-cols-3">
          {FEATURES.map((f) => (
            <div key={f.title} className="flex gap-4 rounded-2xl p-2">
              <f.icon className="mt-1 size-5 shrink-0 text-muted-foreground" />
              <div>
                <h3 className="font-bold">{f.title}</h3>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">{f.body}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-12 text-center">
          <Button asChild size="lg">
            <Link href={cta.href}>{cta.label}</Link>
          </Button>
        </div>
      </section>

      <footer className="border-t py-8 text-center text-xs text-muted-foreground">© 듀얼로그</footer>
    </div>
  );
}
