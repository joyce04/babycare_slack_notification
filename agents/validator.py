"""Validator agent — checks recommendation for age-appropriateness and safety."""

from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import SystemMessage, HumanMessage

import config


VALIDATOR_SYSTEM_PROMPT = """You are a pediatric safety reviewer. Your job is to review a child development recommendation and verify:

1. AGE-APPROPRIATENESS: Is this recommendation suitable for the specified age group?
2. SAFETY: Could this cause harm? Are there choking hazards, injury risks, or unsafe practices?
3. MEDICAL ACCURACY: Are the health claims reasonable and not misleading?
4. REFERENCE VALIDITY: Does the scientific reference look plausible (real journal, reasonable year)?

You MUST respond in this EXACT JSON format (no markdown, no code fences, just raw JSON):
{
    "verdict": "approved" or "rejected",
    "feedback": "Brief explanation of your decision. If rejected, explain what's wrong and suggest a fix."
}

Be strict about safety but reasonable about recommendations. Only reject if there's a genuine concern.
"""


def validator_node(state: dict) -> dict:
    """Validate the recommendation for safety and age-appropriateness."""
    llm = ChatOpenRouter(
        model=config.OPENROUTER_MODEL,
        openrouter_api_key=config.OPENROUTER_API_KEY,
        temperature=0.1,
        max_tokens=512,
    )

    recommendation = state["recommendation"]
    age_group = state["age_group"]

    import json
    human_prompt = (
        f"Review this recommendation for a child aged {age_group} years:\n\n"
        f"{json.dumps(recommendation, indent=2)}\n\n"
        "Is this safe and age-appropriate? Respond with raw JSON only."
    )

    messages = [
        SystemMessage(content=VALIDATOR_SYSTEM_PROMPT),
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
        "validation_result": result["verdict"],
        "validation_feedback": result.get("feedback", ""),
    }
