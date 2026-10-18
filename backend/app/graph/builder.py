from langgraph.graph import END, START, StateGraph

from app.graph import nodes
from app.graph.deps import GraphDeps
from app.graph.state import DebateState


def build_graph() -> StateGraph:
    g = StateGraph(DebateState, context_schema=GraphDeps)
    g.add_node("frame_topic", nodes.frame_topic)
    g.add_node("moderator_round", nodes.moderator_round)
    g.add_node("pro_speech", nodes.pro_speech)
    g.add_node("con_speech", nodes.con_speech)
    g.add_node("round_check", nodes.round_check)
    g.add_node("closing_intro", nodes.closing_intro)
    g.add_node("pro_closing", nodes.pro_closing)
    g.add_node("con_closing", nodes.con_closing)
    g.add_node("summarize", nodes.summarize)

    g.add_edge(START, "frame_topic")
    g.add_edge("frame_topic", "moderator_round")
    g.add_edge("moderator_round", "pro_speech")
    g.add_edge("pro_speech", "con_speech")
    g.add_edge("con_speech", "round_check")
    g.add_conditional_edges(
        "round_check",
        nodes.route_after_round,
        {"moderator_round": "moderator_round", "closing_intro": "closing_intro"},
    )
    g.add_edge("closing_intro", "pro_closing")
    g.add_edge("pro_closing", "con_closing")
    g.add_edge("con_closing", "summarize")
    g.add_edge("summarize", END)
    return g
