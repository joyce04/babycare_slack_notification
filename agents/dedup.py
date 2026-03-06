"""Deduplication agent — uses keyword matching + LLM to check semantic similarity against history."""

from difflib import SequenceMatcher

from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import SystemMessage, HumanMessage

import config


DEDUP_SYSTEM_PROMPT = """You are a STRICT deduplication checker for child development recommendations. Compare a NEW recommendation against PAST recommendations and determine if the new one is too similar.

Mark as DUPLICATE (is_duplicate: true) if ANY of these apply:
- The core topic or activity is the same, even if worded differently (e.g. "Tummy Time Exercise" and "Daily Tummy Time" are duplicates)
- It recommends the same type of toy or book, even with slightly different names (e.g. "Black and White Mobile" and "High Contrast Mobile" are duplicates)
- It covers the same health/safety advice (e.g. "Vitamin D Supplementation" appearing twice)
- The practical advice a parent would follow is essentially the same

Mark as NOT a duplicate (is_duplicate: false) ONLY if:
- It covers a genuinely different activity, topic, or product
- It targets a clearly different developmental area with a different approach
- A parent would learn something meaningfully new from this recommendation

When in doubt, mark it as a DUPLICATE. We prefer variety over repetition.

You MUST respond in this EXACT JSON format (no markdown, no code fences, just raw JSON):
{
    "is_duplicate": true or false,
    "similar_to": "Name of the past recommendation it is most similar to, or empty string if not a duplicate",
    "feedback": "Brief explanation of your reasoning"
}
"""


def _clean(val: str) -> str:
    """Strip control chars, stray quotes, and excessive whitespace for safe prompt embedding."""
    return (
        str(val)
        .replace("\r", " ")
        .replace("\n", " ")
        .replace('"', "'")
        .replace("\\", "")
        .strip()
    )


def _normalize(text: str) -> str:
    """Normalize text for comparison: lowercase, strip punctuation/extra spaces."""
    import re
    text = str(text).lower().strip()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def _quick_duplicate_check(recommendation: dict, history: list[dict]) -> tuple[bool, str]:
    """Fast pre-LLM check for obvious duplicates using name and description similarity.

    Returns:
        (is_duplicate, feedback) tuple
    """
    new_name = _normalize(recommendation.get("name", ""))
    new_desc = _normalize(recommendation.get("description", ""))

    if not new_name:
        return False, ""

    for h in history:
        past_name = _normalize(h.get("name_en", ""))
        past_reasoning = _normalize(h.get("reasoning", ""))

        if not past_name:
            continue

        # Exact name match
        if new_name == past_name:
            return True, f"Exact name match with past recommendation: '{h.get('name_en', '')}'"

        # High name similarity (character-level)
        name_ratio = SequenceMatcher(None, new_name, past_name).ratio()
        if name_ratio >= 0.6:
            return True, f"Very similar name to past recommendation: '{h.get('name_en', '')}' (similarity: {name_ratio:.0%})"

        # Word overlap check (catches "Tummy Time Activity" vs "Tummy Time Exercise")
        new_words = set(new_name.split())
        past_words = set(past_name.split())
        if new_words and past_words:
            common_words = new_words & past_words
            jaccard = len(common_words) / len(new_words | past_words)
            # If most key words overlap, it's likely a duplicate
            if jaccard >= 0.5 and len(common_words) >= 2:
                return True, f"Significant word overlap with past recommendation: '{h.get('name_en', '')}' (shared words: {', '.join(common_words)})"

        # Check if one name is contained in the other
        if len(new_name) > 3 and len(past_name) > 3:
            if new_name in past_name or past_name in new_name:
                return True, f"Name overlap with past recommendation: '{h.get('name_en', '')}'"

        # High description-to-reasoning similarity
        if new_desc and past_reasoning:
            desc_ratio = SequenceMatcher(None, new_desc[:200], past_reasoning[:200]).ratio()
            if desc_ratio >= 0.6:
                return True, f"Very similar content to past recommendation: '{h.get('name_en', '')}' (similarity: {desc_ratio:.0%})"

    return False, ""


def dedup_node(state: dict) -> dict:
    """Check if the recommendation is semantically similar to past recommendations.

    Uses a two-pass approach:
    1. Quick keyword/name similarity check (fast, no LLM call)
    2. LLM semantic similarity check (thorough, catches subtle duplicates)
    """
    history = state.get("history", [])

    # If no history, it can't be a duplicate
    if not history:
        return {
            "is_duplicate": False,
            "dedup_feedback": "No history to compare against.",
        }

    recommendation = state["recommendation"]

    # --- Pass 1: Quick duplicate check (no LLM needed) ---
    is_dup, feedback = _quick_duplicate_check(recommendation, history)
    if is_dup:
        return {
            "is_duplicate": True,
            "dedup_feedback": f"[Quick check] {feedback}",
        }

    # --- Pass 2: LLM semantic similarity check ---
    llm = ChatOpenRouter(
        model=config.OPENROUTER_MODEL,
        openrouter_api_key=config.OPENROUTER_API_KEY,
        temperature=0.1,
        max_tokens=512,
    )

    import json

    # Build a richer history summary (last 30 entries) with reasoning for better semantic matching
    history_lines = []
    for h in history[-30:]:
        line = (
            f"- [{_clean(h.get('date', '?'))}] ({_clean(h.get('type', '?'))}) "
            f"{_clean(h.get('name_en', '?'))} — {_clean(h.get('skill_area', '?'))}"
        )
        reasoning = _clean(h.get("reasoning", ""))
        if reasoning:
            line += f"\n  Summary: {reasoning[:150]}"
        history_lines.append(line)
    history_summary = "\n".join(history_lines)

    human_prompt = (
        f"NEW recommendation:\n"
        f"  Name: {_clean(recommendation.get('name', ''))}\n"
        f"  Category: {_clean(recommendation.get('category', ''))}\n"
        f"  Skill area: {_clean(recommendation.get('skill_area', ''))}\n"
        f"  Description: {_clean(recommendation.get('description', ''))}\n"
        f"  Key steps: {_clean(', '.join(recommendation.get('steps', [])))}\n\n"
        f"PAST recommendations ({len(history)} total):\n{history_summary}\n\n"
        "Is the new recommendation too similar to any past one? "
        "Remember: when in doubt, mark as duplicate. Respond with raw JSON only."
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
