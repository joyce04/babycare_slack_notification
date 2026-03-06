"""Deduplication agent — uses LLM to check semantic similarity against history."""

from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import SystemMessage, HumanMessage

import config


DEDUP_SYSTEM_PROMPT = """You are a deduplication checker. Your job is to compare a NEW recommendation against a list of PAST recommendations and determine if the new one is too similar to any previous one.

A recommendation is considered a DUPLICATE if:
- It covers essentially the same activity, toy, or health topic
- It targets the same skill area with a very similar approach
- The core advice would feel repetitive to a parent who received the previous one

A recommendation is NOT a duplicate if:
- It covers a different activity even if in the same skill area
- It provides a meaningfully different approach to a similar topic
- It targets a different developmental aspect

You MUST respond in this EXACT JSON format (no markdown, no code fences, just raw JSON):
{
    "is_duplicate": true or false,
    "feedback": "Brief explanation. If duplicate, mention which past recommendation it's similar to."
}
"""


def dedup_node(state: dict) -> dict:
    """Check if the recommendation is semantically similar to past recommendations."""
    history = state.get("history", [])

    # If no history, it can't be a duplicate
    if not history:
        return {
            "is_duplicate": False,
            "dedup_feedback": "No history to compare against.",
        }

    llm = ChatOpenRouter(
        model=config.OPENROUTER_MODEL,
        openrouter_api_key=config.OPENROUTER_API_KEY,
        temperature=0.1,
        max_tokens=512,
    )

    import json
    recommendation = state["recommendation"]

    # Sanitise a value so it can be safely embedded in the prompt
    def _clean(val: str) -> str:
        """Strip control chars, stray quotes, and excessive whitespace."""
        return (
            str(val)
            .replace("\r", " ")
            .replace("\n", " ")
            .replace('"', "'")
            .replace("\\", "")
            .strip()
        )

    # Build a concise history summary (last 30 entries)
    history_summary = "\n".join(
        f"- [{_clean(h.get('date', '?'))}] ({_clean(h.get('type', '?'))}) "
        f"{_clean(h.get('name_en', '?'))} — {_clean(h.get('skill_area', '?'))}"
        for h in history[-30:]
    )

    human_prompt = (
        f"NEW recommendation:\n"
        f"  Name: {_clean(recommendation.get('name', ''))}\n"
        f"  Category: {_clean(recommendation.get('category', ''))}\n"
        f"  Skill area: {_clean(recommendation.get('skill_area', ''))}\n"
        f"  Description: {_clean(recommendation.get('description', ''))}\n\n"
        f"PAST recommendations:\n{history_summary}\n\n"
        "Is the new recommendation too similar to any past one? Respond with raw JSON only."
    )

    messages = [
        SystemMessage(content=DEDUP_SYSTEM_PROMPT),
        HumanMessage(content=human_prompt),
    ]

    response = llm.invoke(messages)
    content = response.content.strip()

    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3].strip()

    result = json.loads(content)

    return {
        "is_duplicate": result["is_duplicate"],
        "dedup_feedback": result.get("feedback", ""),
    }
