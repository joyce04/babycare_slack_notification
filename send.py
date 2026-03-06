"""Workflow 2: Send — randomly picks an unsent recommendation from CSV and sends to Slack.

Usage:
    python send.py              # Send one random unsent recommendation to Slack
    python send.py --dry-run    # Preview without sending
"""

import argparse
import json
import random
import sys
from datetime import date

import config
from tracker import get_unsent_recommendations, mark_as_sent
from slack_sender import send_slack_message


CATEGORY_HEADERS = {
    "exercise": "🏃 Exercise / 운동",
    "toy": "🧸 Toy Recommendation / 장난감 추천",
    "health_tip": "🩺 Health Tip / 건강 팁",
}


def build_slack_payload(rec: dict) -> dict:
    """Build a Slack Block Kit payload from a CSV recommendation row."""
    child_name = config.CHILD_NAME
    today = date.today().strftime("%B %d, %Y")
    category = rec.get("type", "")
    category_header = CATEGORY_HEADERS.get(category, "📌 Recommendation")
    age_group = rec.get("age_group", "?")
    english_content = rec.get("english_content", "")
    korean_content = rec.get("korean_content", "")

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🌅 Good Morning! Today's Recommendation for {child_name}",
                "emoji": True,
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"📅 {today}  •  👶 Age: {age_group}  •  {category_header}",
                },
            ],
        },
        {"type": "divider"},
        # {
        #     "type": "section",
        #     "text": {
        #         "type": "mrkdwn",
        #         "text": f"🇺🇸 *English*\n\n{english_content}",
        #     },
        # },
        # {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"🇰🇷 *한국어*\n\n{korean_content}",
            },
        },
        {"type": "divider"},
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

    return {"blocks": blocks}


def print_preview(payload: dict) -> None:
    """Pretty-print a Slack Block Kit payload to the console."""
    print("\n" + "=" * 60)
    print("📨 SLACK MESSAGE PREVIEW")
    print("=" * 60)
    for block in payload.get("blocks", []):
        if block["type"] == "header":
            print(f"\n{'=' * 50}")
            print(f"  {block['text']['text']}")
            print(f"{'=' * 50}")
        elif block["type"] == "section":
            print(f"\n{block['text']['text']}")
        elif block["type"] == "context":
            for elem in block["elements"]:
                print(f"\n  {elem['text']}")
        elif block["type"] == "divider":
            print("—" * 50)
    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Workflow 2: Send a random unsent recommendation to Slack",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python send.py              # Send to Slack
  python send.py --dry-run    # Preview in console
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print to console instead of sending to Slack",
    )
    args = parser.parse_args()

    # Check config
    if not args.dry_run and not config.SLACK_WEBHOOK_URL:
        print("❌ SLACK_WEBHOOK_URL not set. Use --dry-run or configure .env")
        sys.exit(1)

    # Compute current child age
    current_age = config.get_child_age()
    if not current_age:
        print("❌ Could not determine child age. Set CHILD_BIRTHDATE in .env")
        sys.exit(1)

    print(f"👶 Current child age: {current_age}")

    # Get unsent recommendations
    unsent = get_unsent_recommendations(config.CSV_PATH)

    if not unsent:
        print("⚠️  No unsent recommendations in CSV. Run 'python collect.py' first!")
        sys.exit(1)

    # Filter to recommendations matching the current age
    age_matched = [r for r in unsent if r.get("age_group") == current_age]

    if age_matched:
        pool = age_matched
        print(f"📋 Found {len(age_matched)} unsent recommendation(s) for age: {current_age}")
    else:
        pool = unsent
        print(f"⚠️  No unsent recommendations for exact age '{current_age}'.")
        print(f"   Falling back to all {len(unsent)} unsent recommendation(s).")
        print(f"   💡 Run 'python collect.py' to generate age-appropriate recommendations.")

    # Randomly pick one
    selected = random.choice(pool)
    print(f"🎲 Selected: [{selected.get('type')}] {selected.get('name_en')}")
    print(f"   Age group: {selected.get('age_group')}")
    print(f"   Skill area: {selected.get('skill_area')}")

    # Build Slack payload
    payload = build_slack_payload(selected)

    if args.dry_run:
        print_preview(payload)
    else:
        print("\n📨 Sending to Slack...")
        success = send_slack_message(config.SLACK_WEBHOOK_URL, payload)
        if not success:
            print("❌ Failed to send Slack message")
            sys.exit(1)
        print("✅ Slack message sent successfully!")

    # Mark as sent in CSV
    mark_as_sent(
        config.CSV_PATH,
        target_date=selected.get("date", ""),
        target_name=selected.get("name_en", ""),
    )
    print(f"📝 Marked as sent in {config.CSV_PATH}")


if __name__ == "__main__":
    main()
