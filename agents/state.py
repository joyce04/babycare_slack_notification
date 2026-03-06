"""LangGraph shared state definition for the recommendation pipeline."""

from typing import TypedDict


class RecommendationState(TypedDict):
    """Shared state passed through all agent nodes in the graph."""

    # --- Input ---
    age_group: str           # e.g. "0-1", "1-3", "3-5", "5-8", "8-12"
    category: str            # Randomly chosen: "exercise", "toy", or "health_tip"

    # --- Researcher output ---
    recommendation: dict     # Structured recommendation from researcher
                             # Keys: name, description, steps (list), duration,
                             #        skill_area, emoji, reasoning,
                             #        reference_text, reference_link,
                             #        amazon_link (toy only)

    # --- Validator output ---
    validation_result: str   # "approved" or "rejected"
    validation_feedback: str # Reason if rejected

    # --- Dedup output ---
    is_duplicate: bool       # True if semantically similar to history
    dedup_feedback: str      # Explanation of similarity

    # --- Translator output ---
    english_content: str     # Formatted English text
    korean_content: str      # Formatted Korean text

    # --- Formatter output ---
    slack_payload: dict      # Slack Block Kit JSON

    # --- Context ---
    history: list            # Past recommendations loaded from CSV
    retry_count: int         # Number of retries (max 3)
    rejected_names: list     # Names rejected by validator or dedup (fed back to researcher)
    error: str               # Error message if any
