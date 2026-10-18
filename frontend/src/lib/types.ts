export type DebateStatus = "running" | "completed" | "stopped" | "failed";
export type Speaker = "moderator" | "pro" | "con";
export type Phase = "opening_remarks" | "moderation" | "opening" | "rebuttal" | "closing";

export const CLOSING_ROUND = 99;

export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface DebateListItem {
  id: string;
  topic_raw: string;
  proposition: string | null;
  status: DebateStatus;
  current_round: number;
  total_rounds: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface Turn {
  seq: number;
  round: number;
  phase: Phase;
  speaker: Speaker;
  content: string;
  search_queries: string[];
}

export interface Source {
  number: number;
  url: string;
  title: string;
  published_date: string | null;
  author: string | null;
  excerpt: string;
}

export interface FinalSummary {
  overview: string;
  key_issues: string[];
  agreements: string[];
  disagreements: string[];
  open_questions: string[];
}

export interface Summary {
  pro_summary: string;
  con_summary: string;
  final_summary: FinalSummary;
}

export interface DebateDetail extends DebateListItem {
  pro_stance: string | null;
  con_stance: string | null;
  error: string | null;
  turns: Turn[];
  sources: Source[];
  summary: Summary | null;
}

export interface PartialTurn {
  seq: number;
  speaker: Speaker;
  round: number;
  phase: Phase;
  text: string;
  searches: string[];
}

export interface RoundDecision {
  round: number;
  continue: boolean;
  reason: string;
}
