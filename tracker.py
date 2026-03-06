"""CSV tracker — reads/writes recommendation history and manages send status."""

import csv
import json
import os
from datetime import date


CSV_HEADERS = [
    "date",
    "type",
    "name_en",
    "name_kr",
    "age_group",
    "skill_area",
    "reasoning",
    "reference",
    "reference_link",
    "english_content",
    "korean_content",
    "amazon_link",
    "sent",
]


def load_history(csv_path: str) -> list[dict]:
    """Load past recommendations from CSV. Returns list of dicts."""
    if not os.path.exists(csv_path):
        return []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def get_unsent_recommendations(csv_path: str) -> list[dict]:
    """Get all recommendations that haven't been sent yet."""
    history = load_history(csv_path)
    return [r for r in history if r.get("sent", "false").lower() == "false"]


def mark_as_sent(csv_path: str, target_date: str, target_name: str) -> bool:
    """Mark a specific recommendation as sent in the CSV.

    Args:
        csv_path: Path to recommendations CSV.
        target_date: Date of the recommendation row.
        target_name: English name of the recommendation row.

    Returns:
        True if the row was found and updated.
    """
    rows = load_history(csv_path)
    updated = False

    for row in rows:
        if row.get("date") == target_date and row.get("name_en") == target_name:
            row["sent"] = "true"
            updated = True
            break

    if updated:
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerows(rows)

    return updated


def log_recommendation(
    csv_path: str,
    recommendation: dict,
    korean_name: str,
    age_group: str,
    english_content: str = "",
    korean_content: str = "",
) -> None:
    """Append a recommendation to the CSV file."""
    file_exists = os.path.exists(csv_path) and os.path.getsize(csv_path) > 0

    with open(csv_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "date": date.today().isoformat(),
            "type": recommendation.get("category", ""),
            "name_en": recommendation.get("name", ""),
            "name_kr": korean_name,
            "age_group": age_group,
            "skill_area": recommendation.get("skill_area", ""),
            "reasoning": recommendation.get("reasoning", ""),
            "reference": recommendation.get("reference_text", ""),
            "reference_link": recommendation.get("reference_link", ""),
            "english_content": english_content,
            "korean_content": korean_content,
            "amazon_link": recommendation.get("amazon_link", ""),
            "sent": "false",
        })

