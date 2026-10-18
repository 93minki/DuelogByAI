import { DebateView } from "@/components/debate/debate-view";

export const metadata = { title: "토론 — 듀얼로그" };

export default async function DebatePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <DebateView debateId={id} />;
}
