"""Configuration loader for the daily child development alert system."""

import os
from datetime import date, datetime
from dotenv import load_dotenv

load_dotenv()

# --- OpenRouter ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")

# --- Slack ---
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

# --- Child ---
CHILD_BIRTHDATE = os.getenv("CHILD_BIRTHDATE", "")  # Format: YYYY-MM-DD
CHILD_NAME = os.getenv("CHILD_NAME", "Baby")

# --- Paths ---
CSV_PATH = os.path.join(os.path.dirname(__file__), "recommendations.csv")

# --- Recommendation categories ---
CATEGORIES = ["exercise", "toy", "health_tip", "book", "development_tip", "safety_tip"]


def get_child_age() -> str:
    """Compute a human-readable age string from CHILD_BIRTHDATE.

    Returns:
        e.g. "2 months", "14 months", "3 years 2 months"
    """
    if not CHILD_BIRTHDATE:
        return ""

    try:
        birth = datetime.strptime(CHILD_BIRTHDATE, "%Y-%m-%d").date()
    except ValueError:
        print(f"⚠️  Invalid CHILD_BIRTHDATE format: {CHILD_BIRTHDATE}. Use YYYY-MM-DD.")
        return ""

    today = date.today()
    total_months = (today.year - birth.year) * 12 + (today.month - birth.month)

    # Adjust if the day hasn't passed yet this month
    if today.day < birth.day:
        total_months -= 1

    if total_months < 0:
        return "0 months"

    if total_months < 24:
        return f"{total_months} months"

    years = total_months // 12
    remaining_months = total_months % 12
    if remaining_months == 0:
        return f"{years} years"
    return f"{years} years {remaining_months} months"
