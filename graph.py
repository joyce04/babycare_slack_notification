"""LangGraph graph definition — wires up all agents with conditional retry loops."""

import random

from langgraph.graph import StateGraph, END

from agents.state import RecommendationState
from agents.researcher import researcher_node
from agents.validator import validator_node
from agents.dedup import dedup_node
from agents.translator import translator_node

import config


def pick_category_node(state: dict) -> dict:
    """Randomly select a recommendation category."""
    category = random.choice(config.CATEGORIES)
    return {"category": category, "retry_count": 0}


def increment_retry_node(state: dict) -> dict:
    """Increment retry count and pick a new category on retry."""
    new_category = random.choice(config.CATEGORIES)
    return {
        "retry_count": state.get("retry_count", 0) + 1,
        "category": new_category,
    }


# --- Conditional edge functions ---

def after_validation(state: dict) -> str:
    """Route after validation: approved → dedup, rejected → retry or end."""
    if state.get("validation_result") == "approved":
        return "dedup"
    if state.get("retry_count", 0) >= 3:
        return "end"
    return "retry"


def after_dedup(state: dict) -> str:
    """Route after dedup: pass → translate, duplicate → retry or end."""
    if not state.get("is_duplicate", False):
        return "translate"
    if state.get("retry_count", 0) >= 3:
        return "end"
    return "retry"


def build_graph() -> StateGraph:
    """Build and compile the recommendation collection pipeline.

    Pipeline: pick_category → research → validate → dedup → translate → END
    Formatting is handled separately in send.py.
    """
    graph = StateGraph(RecommendationState)

    # --- Add nodes ---
    graph.add_node("pick_category", pick_category_node)
    graph.add_node("research", researcher_node)
    graph.add_node("validate", validator_node)
    graph.add_node("dedup", dedup_node)
    graph.add_node("translate", translator_node)
    graph.add_node("retry", increment_retry_node)

    # --- Set entry point ---
    graph.set_entry_point("pick_category")

    # --- Linear edges ---
    graph.add_edge("pick_category", "research")
    graph.add_edge("research", "validate")

    # --- Conditional: after validation ---
    graph.add_conditional_edges(
        "validate",
        after_validation,
        {
            "dedup": "dedup",
            "retry": "retry",
            "end": END,
        },
    )

    # --- Conditional: after dedup ---
    graph.add_conditional_edges(
        "dedup",
        after_dedup,
        {
            "translate": "translate",
            "retry": "retry",
            "end": END,
        },
    )

    # --- Retry loops back to research ---
    graph.add_edge("retry", "research")

    # --- Translate → END (formatting happens in send.py) ---
    graph.add_edge("translate", END)

    return graph.compile()

