"""Formatter agent — builds Slack Block Kit message from bilingual content."""

from datetime import date

import config


CATEGORY_HEADERS = {
    "exercise": "🏃 Exercise / 운동",
    "toy": "🧸 Toy Recommendation / 장난감 추천",
    "health_tip": "🩺 Health Tip / 건강 팁",
}


def formatter_node(state: dict) -> dict:
    """Build a Slack Block Kit payload from bilingual content."""
    recommendation = state["recommendation"]
    english_content = state["english_content"]
    korean_content = state["korean_content"]
    age_group = state["age_group"]
    category = state["category"]
    child_name = config.CHILD_NAME

    today = date.today().strftime("%B %d, %Y")
    category_header = CATEGORY_HEADERS.get(category, "📌 Recommendation")

    blocks = [
        # --- Header ---
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🌅 Good Morning! Today's Recommendation for {child_name}",
                "emoji": True,
            },
        },
        # --- Date & category context ---
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"📅 {today}  •  👶 Age: {age_group} yr  •  {category_header}",
                },
            ],
        },
        {"type": "divider"},
        # --- English section ---
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"🇺🇸 *English*\n\n{english_content}",
            },
        },
        {"type": "divider"},
        # --- Korean section ---
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"🇰🇷 *한국어*\n\n{korean_content}",
            },
        },
        {"type": "divider"},
        # --- Footer ---
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "💛 _Powered by Daily Child Dev Alert_ • Reply ✅ when completed!",
                },
            ],
        },
    ]

    return {"slack_payload": {"blocks": blocks}}
