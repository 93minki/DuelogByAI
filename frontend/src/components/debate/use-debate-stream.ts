"use client";

import { useEffect, useReducer } from "react";

import type { DebateDetail, PartialTurn, RoundDecision, Source, Summary, Turn } from "@/lib/types";

interface State {
  debate: DebateDetail | null;
  partial: PartialTurn | null;
  decisions: RoundDecision[];
  connection: "connecting" | "open" | "closed";
}

type Action =
  | { type: "snapshot"; data: DebateDetail & { partial: PartialTurn | null } }
  | { type: "event"; name: string; data: Record<string, unknown> }
  | { type: "connection"; value: State["connection"] };

function mergeSources(existing: Source[], incoming: Source[]): Source[] {
  const seen = new Set(existing.map((s) => s.number));
  return [...existing, ...incoming.filter((s) => !seen.has(s.number))].sort((a, b) => a.number - b.number);
}

function reducer(state: State, action: Action): State {
  if (action.type === "connection") return { ...state, connection: action.value };
  if (action.type === "snapshot") {
    const { partial, ...debate } = action.data;
    return { ...state, debate, partial };
  }
  const debate = state.debate;
  if (!debate) return state;
  const d = action.data;

  switch (action.name) {
    case "framed":
      return {
        ...state,
        debate: {
          ...debate,
          proposition: d.proposition as string,
          pro_stance: d.pro_stance as string,
          con_stance: d.con_stance as string,
        },
      };
    case "round":
      return { ...state, debate: { ...debate, current_round: d.round as number } };
    case "turn_start":
      return { ...state, partial: { ...(d as unknown as PartialTurn), text: "", searches: [] } };
    case "search":
      if (!state.partial || state.partial.seq !== d.seq) return state;
      return { ...state, partial: { ...state.partial, searches: [...state.partial.searches, d.query as string] } };
    case "token":
      if (!state.partial || state.partial.seq !== d.seq) return state;
      return { ...state, partial: { ...state.partial, text: state.partial.text + (d.delta as string) } };
    case "turn_reset":
      if (!state.partial || state.partial.seq !== d.seq) return state;
      return { ...state, partial: { ...state.partial, text: "" } };
    case "turn_end": {
      const turn = d.turn as Turn;
      const turns = debate.turns.some((t) => t.seq === turn.seq)
        ? debate.turns.map((t) => (t.seq === turn.seq ? turn : t))
        : [...debate.turns, turn].sort((a, b) => a.seq - b.seq);
      return {
        ...state,
        partial: state.partial?.seq === turn.seq ? null : state.partial,
        debate: { ...debate, turns, sources: mergeSources(debate.sources, d.sources as Source[]) },
      };
    }
    case "round_decision": {
      const decision = d as unknown as RoundDecision;
      return {
        ...state,
        decisions: [...state.decisions.filter((x) => x.round !== decision.round), decision],
        debate: decision.continue ? debate : { ...debate, total_rounds: decision.round },
      };
    }
    case "summary":
      return { ...state, debate: { ...debate, summary: d as unknown as Summary } };
    case "status":
      return {
        ...state,
        partial: null,
        debate: { ...debate, status: d.status as DebateDetail["status"], error: (d.error as string) ?? null },
      };
    default:
      return state;
  }
}

const EVENTS = [
  "framed",
  "round",
  "turn_start",
  "search",
  "token",
  "turn_reset",
  "turn_end",
  "round_decision",
  "summary",
  "status",
];

/** SSE로 토론을 구독한다. 첫 이벤트(snapshot)가 DB 기준 전체 상태이고, 이후 실시간 이벤트가 이어진다. */
export function useDebateStream(debateId: string) {
  const [state, dispatch] = useReducer(reducer, {
    debate: null,
    partial: null,
    decisions: [],
    connection: "connecting",
  });

  useEffect(() => {
    const es = new EventSource(`/api/debates/${debateId}/stream`, { withCredentials: true });
    es.addEventListener("snapshot", (e) => {
      const data = JSON.parse((e as MessageEvent).data);
      dispatch({ type: "snapshot", data });
      dispatch({ type: "connection", value: "open" });
      if (data.status !== "running") {
        es.close();
        dispatch({ type: "connection", value: "closed" });
      }
    });
    for (const name of EVENTS) {
      es.addEventListener(name, (e) => {
        const data = JSON.parse((e as MessageEvent).data);
        dispatch({ type: "event", name, data });
        if (name === "status") {
          es.close();
          dispatch({ type: "connection", value: "closed" });
        }
      });
    }
    // 연결이 끊기면 EventSource가 자동 재연결하고, 서버가 snapshot부터 다시 보낸다.
    es.onerror = () => {
      if (es.readyState === EventSource.CONNECTING) dispatch({ type: "connection", value: "connecting" });
    };
    return () => es.close();
  }, [debateId]);

  return state;
}
