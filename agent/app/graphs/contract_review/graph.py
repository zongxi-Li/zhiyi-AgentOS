from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.graphs.contract_review.nodes import (
    classify_clauses_node,
    human_review_node,
    legal_evidence_match_node,
    parse_contract_node,
    report_generate_node,
    risk_detect_node,
    suggestion_generate_node,
)
from app.graphs.contract_review.state import ContractReviewState


def build_contract_review_graph():
    builder = StateGraph(ContractReviewState)
    builder.add_node("parse_contract", parse_contract_node)
    builder.add_node("classify_clauses", classify_clauses_node)
    builder.add_node("risk_detect", risk_detect_node)
    builder.add_node("legal_evidence_match", legal_evidence_match_node)
    builder.add_node("suggestion_generate", suggestion_generate_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("report_generate", report_generate_node)
    builder.add_edge(START, "parse_contract")
    builder.add_edge("parse_contract", "classify_clauses")
    builder.add_edge("classify_clauses", "risk_detect")
    builder.add_edge("risk_detect", "legal_evidence_match")
    builder.add_edge("legal_evidence_match", "suggestion_generate")
    builder.add_edge("suggestion_generate", "human_review")
    builder.add_edge("human_review", "report_generate")
    builder.add_edge("report_generate", END)
    return builder.compile(checkpointer=InMemorySaver(), interrupt_before=["report_generate"])
