"""Translator agent — translates recommendation content to Korean."""

from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import SystemMessage, HumanMessage

import config


TRANSLATOR_SYSTEM_PROMPT = """You are a professional Korean translator specializing in parenting and child development content. Your job is to translate a child development recommendation from English to Korean.

RULES:
1. Translate naturally — use native Korean parenting vocabulary, not literal translations.
2. PRESERVE all links (DOI links, Amazon links) exactly as-is — do NOT translate URLs.
3. PRESERVE scientific reference citations in their original English form.
4. Translate the recommendation name, description, steps, reasoning, and skill area.
5. Use 존댓말 (polite/formal speech level) appropriate for a morning parenting message.

You MUST respond in this EXACT JSON format (no markdown, no code fences, just raw JSON):
{
    "name_kr": "Korean name",
    "description_kr": "Korean description",
    "steps_kr": ["Korean step 1", "Korean step 2", "Korean step 3"],
    "reasoning_kr": "Korean reasoning",
    "skill_area_kr": "Korean skill area name"
}
"""


def translator_node(state: dict) -> dict:
    """Translate recommendation content to Korean."""
    llm = ChatOpenRouter(
        model=config.OPENROUTER_MODEL,
        openrouter_api_key=config.OPENROUTER_API_KEY,
        temperature=0.3,
        max_tokens=1024,
    )

    import json
    recommendation = state["recommendation"]

    human_prompt = (
        f"Translate this child development recommendation to Korean:\n\n"
        f"{json.dumps(recommendation, indent=2, ensure_ascii=False)}\n\n"
        "Respond with raw JSON only. Preserve all links and citations in English."
    )

    messages = [
        SystemMessage(content=TRANSLATOR_SYSTEM_PROMPT),
        HumanMessage(content=human_prompt),
    ]

    response = llm.invoke(messages)
    content = response.content.strip()

    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3].strip()

    translation = json.loads(content)

    # Build formatted English content
    rec = recommendation
    steps_en = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(rec.get("steps", [])))
    english_content = (
        f"{rec.get('emoji', '📌')} *{rec['name']}* ({rec.get('skill_area', '')})\n"
        f"{rec['description']}\n\n"
        f"*Steps:*\n{steps_en}\n\n"
        f"⏱ Duration: {rec.get('duration', 'N/A')}\n\n"
        f"💡 *Why this matters:*\n{rec.get('reasoning', '')}\n\n"
        f"📚 *Reference:*\n{rec.get('reference_text', '')}\n"
        f"🔗 {rec.get('reference_link', '')}"
    )

    # Add Amazon link for toys
    if rec.get("amazon_link"):
        english_content += f"\n🛒 <{rec['amazon_link']}|Shop on Amazon>"

    # Build formatted Korean content
    steps_kr = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(translation.get("steps_kr", [])))
    korean_content = (
        f"{rec.get('emoji', '📌')} *{translation['name_kr']}* ({translation.get('skill_area_kr', '')})\n"
        f"{translation['description_kr']}\n\n"
        f"*단계:*\n{steps_kr}\n\n"
        f"⏱ 시간: {rec.get('duration', 'N/A')}\n\n"
        f"💡 *이 활동이 중요한 이유:*\n{translation.get('reasoning_kr', '')}\n\n"
        f"📚 *참고문헌:*\n{rec.get('reference_text', '')}\n"
        f"🔗 {rec.get('reference_link', '')}"
    )

    if rec.get("amazon_link"):
        korean_content += f"\n🛒 <{rec['amazon_link']}|아마존에서 구매>"

    return {
        "english_content": english_content,
        "korean_content": korean_content,
    }
