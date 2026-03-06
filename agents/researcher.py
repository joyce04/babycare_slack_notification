"""Researcher agent — generates a child development recommendation with scientific backing."""

from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import SystemMessage, HumanMessage

import config


RESEARCHER_SYSTEM_PROMPT = """You are a pediatric child development expert. Your job is to generate ONE specific, actionable recommendation for a parent based on the child's age group and the given category.

IMPORTANT RULES:
1. Provide REAL scientific/medical references with verifiable links. Use DOI links for journal articles, or official URLs from reputable authorities (CDC, AAP, WHO, NHS, HealthyChildren.org, etc.). Do NOT fabricate references.
2. Include clear reasoning for WHY this recommendation benefits the child at their specific age.
3. Be specific and practical — parents should be able to act on this immediately.
4. Use well-known, widely-cited research from reputable journals (AAP Pediatrics, JAMA Pediatrics, Developmental Psychology, etc.) or official guidelines from medical authorities (CDC, AAP, WHO, Mayo Clinic, etc.).

You MUST respond in this EXACT JSON format (no markdown, no code fences, just raw JSON):
{
    "name": "Short descriptive name of the recommendation",
    "description": "One paragraph describing what this recommendation involves",
    "steps": ["Step 1 description", "Step 2 description", "Step 3 description"],
    "duration": "Recommended duration (e.g. '10-15 minutes')",
    "skill_area": "Primary developmental area (e.g. 'Gross Motor', 'Fine Motor', 'Cognitive', 'Language', 'Social-Emotional', 'Sensory')",
    "emoji": "One relevant emoji",
    "reasoning": "2-3 sentences explaining WHY this recommendation specifically benefits children in this age group, referencing developmental milestones",
    "reference_text": "Author(s) (Year). Title. Journal Name, Volume(Issue), Pages.",
    "reference_link": "https://doi.org/10.xxxx/xxxxx or https://www.cdc.gov/... or other official URL"
}

FOR TOY or BOOK RECOMMENDATIONS, also include:
    "amazon_link": "https://www.amazon.com/s?k=url+encoded+toy+or+book+name"

Age group developmental context (adapt to the specific age given):
- 0-3 months: Reflexes, head lifting, visual tracking, cooing, skin-to-skin bonding
- 4-6 months: Rolling over, reaching/grasping, babbling, recognizing faces, tummy time
- 7-9 months: Sitting, crawling, passing objects between hands, stranger anxiety, peek-a-boo
- 10-12 months: Pulling to stand, pincer grasp, first words, object permanence, waving
- 13-18 months: First steps, stacking 2-3 blocks, 10+ words, pointing, parallel play
- 19-24 months: Running, scribbling, two-word phrases, pretend play, sorting shapes
- 2-3 years: Climbing, simple puzzles, sentences, cooperative play, potty training readiness
- 3-5 years: Running/jumping, scissors use, letter recognition, cooperative play, emotional regulation
- 5-8 years: Sports skills, reading/writing, complex puzzles, teamwork, empathy development
- 8-12 years: Advanced coordination, critical thinking, creative projects, peer relationships, independence
"""


def researcher_node(state: dict) -> dict:
    """Generate a recommendation based on age group and category."""
    llm = ChatOpenRouter(
        model=config.OPENROUTER_MODEL,
        openrouter_api_key=config.OPENROUTER_API_KEY,
        temperature=0.8,
        max_tokens=1024,
    )

    age_group = state["age_group"]
    category = state["category"]

    category_descriptions = {
        "exercise": "a physical exercise or motor skill activity the parent can do WITH their child",
        "toy": "an age-appropriate toy or play item that promotes development (include an Amazon search link)",
        "health_tip": "an important health, nutrition, or developmental tip backed by medical evidence",
        "book": "an age-appropriate book recommendation that supports cognitive or language development (include an Amazon search link)",
        "development_tip": "a practical developmental milestone tip or activity that helps the child reach age-appropriate milestones",
        "safety_tip": "an important child safety tip or precaution relevant to the child's current age and developmental stage",
    }

    human_prompt = (
        f"Generate ONE {category_descriptions[category]} for a child aged {age_group}.\n\n"
        f"Category: {category}\n"
        f"Child's age: {age_group}\n\n"
        "Remember: Use REAL references with REAL DOI links. Respond with raw JSON only."
    )

    messages = [
        SystemMessage(content=RESEARCHER_SYSTEM_PROMPT),
        HumanMessage(content=human_prompt),
    ]

    response = llm.invoke(messages)
    content = response.content.strip()

    # Strip markdown code fences if the LLM wraps them
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3].strip()

    import json
    recommendation = json.loads(content)
    recommendation["category"] = category

    return {"recommendation": recommendation}
