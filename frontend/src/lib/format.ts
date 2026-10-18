import { CLOSING_ROUND, type DebateStatus, type Phase, type Speaker } from "@/lib/types";

export const SPEAKER_LABEL: Record<Speaker, string> = {
  moderator: "사회자",
  pro: "찬성",
  con: "반대",
};

export const PHASE_LABEL: Record<Phase, string> = {
  opening_remarks: "개회",
  moderation: "진행",
  opening: "입론",
  rebuttal: "반박",
  closing: "최종 발언",
};

export const STATUS_LABEL: Record<DebateStatus, string> = {
  running: "진행 중",
  completed: "완료",
  stopped: "중단됨",
  failed: "실패",
};

export function roundLabel(round: number): string {
  if (round === 0) return "개회";
  if (round === CLOSING_ROUND) return "최종 발언";
  return `${round}라운드`;
}

export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

export function hostname(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}
