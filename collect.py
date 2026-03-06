"""Workflow 1: Collect — runs the LangGraph pipeline and saves recommendations to CSV.

Usage:
    python collect.py --age-group "6 months"            # Collect one recommendation
    python collect.py --age-group "2 months" --count 5  # Collect 5 recommendations
"""

import argparse
import json
import sys

import config
from graph import build_graph
from tracker import load_history, log_recommendation


def extract_korean_name(korean_content: str) -> str:
    """Extract the Korean name from formatted Korean content."""
    try:
        start = korean_content.index("*") + 1
        end = korean_content.index("*", start)
        return korean_content[start:end]
    except (ValueError, IndexError):
        return ""


def collect_one(age_group: str) -> bool:
    """Run the LangGraph pipeline once and save to CSV.

    Returns:
        True if a recommendation was successfully collected.
    """
    # Load history for dedup
    history = load_history(config.CSV_PATH)
    print(f"📋 Loaded {len(history)} past recommendations from CSV")

    # Build and run the graph
    graph = build_graph()

    initial_state = {
        "age_group": age_group,
        "category": "",
        "recommendation": {},
        "validation_result": "",
        "validation_feedback": "",
        "is_duplicate": False,
        "dedup_feedback": "",
        "english_content": "",
        "korean_content": "",
        "slack_payload": {},
        "history": history,
        "retry_count": 0,
        "rejected_names": [],
        "error": "",
    }

    print("🤖 Running multi-agent pipeline...")

    try:
        result = graph.invoke(initial_state)
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        return False

    # Check if we got valid bilingual content
    if not result.get("english_content") or not result.get("korean_content"):
        print(f"❌ Pipeline did not produce valid content after {result.get('retry_count', 0)} retries.")
        if result.get("validation_feedback"):
            print(f"   Validation: {result['validation_feedback']}")
        if result.get("dedup_feedback"):
            print(f"   Dedup: {result['dedup_feedback']}")
        return False

    recommendation = result["recommendation"]
    korean_name = extract_korean_name(result.get("korean_content", ""))

    # Log to CSV (with sent=false)
    log_recommendation(
        csv_path=config.CSV_PATH,
        recommendation=recommendation,
        korean_name=korean_name,
        age_group=age_group,
        english_content=result["english_content"],
        korean_content=result["korean_content"],
    )

    print(f"✅ Collected: [{recommendation.get('category')}] {recommendation.get('name')}")
    print(f"   Skill area: {recommendation.get('skill_area')}")
    print(f"   Reference: {recommendation.get('reference_text', 'N/A')}")
    print(f"📝 Saved to {config.CSV_PATH} (sent=false)")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Workflow 1: Collect child development recommendations into CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python collect.py                                   # Use age from birthdate in .env
  python collect.py --count 5                         # Collect 5 recommendations
  python collect.py --age "6 months" --count 3        # Override age manually
        """,
    )
    parser.add_argument(
        "--age",
        type=str,
        default=None,
        help="Override child age (e.g. '2 months', '3 years'). Default: computed from CHILD_BIRTHDATE in .env",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of recommendations to collect (default: 1)",
    )
    args = parser.parse_args()

    age_group = args.age or config.get_child_age()

    if not age_group:
        print("❌ Could not determine child age. Set CHILD_BIRTHDATE in .env or use --age")
        sys.exit(1)

    if not config.OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY not set. Configure .env")
        sys.exit(1)

    print(f"🔬 Collecting {args.count} recommendation(s) for age: {age_group}")
    print(f"   Model: {config.OPENROUTER_MODEL}")
    print()

    successes = 0
    for i in range(args.count):
        if args.count > 1:
            print(f"\n{'='*50}")
            print(f"  Recommendation {i+1} of {args.count}")
            print(f"{'='*50}")

        if collect_one(age_group):
            successes += 1

    print(f"\n📊 Summary: {successes}/{args.count} recommendations collected")
    sys.exit(0 if successes > 0 else 1)


if __name__ == "__main__":
    main()
