import type { DebateDetail, DebateListItem, User } from "@/lib/types";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail: unknown,
  ) {
    super(message);
  }
}

function messageFrom(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    // FastAPI 검증 오류: [{loc: ["body", "email"], msg: "..."}]
    const first = detail[0] as { loc?: unknown[]; msg?: string };
    const field = first.loc?.[first.loc.length - 1];
    if (field === "email") return "올바른 이메일 주소를 입력해 주세요.";
    if (field === "password") return "비밀번호는 8자 이상 128자 이하로 입력해 주세요.";
    return String(first.msg ?? fallback).replace(/^Value error,\s*/, "");
  }
  if (detail && typeof detail === "object" && "message" in detail) {
    return String((detail as { message: unknown }).message);
  }
  return fallback;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    let detail: unknown = null;
    try {
      detail = (await res.json()).detail;
    } catch {
      /* 본문 없음 */
    }
    if (res.status === 401 && typeof window !== "undefined" && !path.startsWith("/api/auth/")) {
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- 상태를 비우려고 전체 새로고침
      window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
    }
    throw new ApiError(res.status, messageFrom(detail, "요청을 처리하지 못했습니다."), detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  signup: (email: string, password: string) =>
    request<User>("/api/auth/signup", { method: "POST", body: JSON.stringify({ email, password }) }),
  login: (email: string, password: string) =>
    request<User>("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  logout: () => request<void>("/api/auth/logout", { method: "POST" }),
  me: () => request<User>("/api/auth/me"),

  listDebates: () => request<DebateListItem[]>("/api/debates"),
  createDebate: (topic: string) =>
    request<DebateListItem>("/api/debates", { method: "POST", body: JSON.stringify({ topic }) }),
  getDebate: (id: string) => request<DebateDetail>(`/api/debates/${id}`),
  stopDebate: (id: string) => request<DebateListItem>(`/api/debates/${id}/stop`, { method: "POST" }),
  deleteDebate: (id: string) => request<void>(`/api/debates/${id}`, { method: "DELETE" }),
};

export interface TopicVerdictDetail {
  status: "rejected" | "ambiguous";
  reason: string | null;
  message: string;
}

export function topicVerdictFrom(error: unknown): TopicVerdictDetail | null {
  if (error instanceof ApiError && error.status === 422) {
    const d = error.detail as Partial<TopicVerdictDetail> | null;
    if (d && typeof d === "object" && (d.status === "rejected" || d.status === "ambiguous")) {
      return d as TopicVerdictDetail;
    }
  }
  return null;
}
