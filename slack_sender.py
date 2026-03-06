"""Slack sender — posts Block Kit messages via Incoming Webhook."""

import json
import requests


def send_slack_message(webhook_url: str, payload: dict) -> bool:
    """Send a Slack Block Kit message via webhook.

    Args:
        webhook_url: Slack Incoming Webhook URL.
        payload: Dict with 'blocks' key containing Block Kit blocks.

    Returns:
        True if message was sent successfully, False otherwise.
    """
    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if response.status_code == 200 and response.text == "ok":
            return True
        else:
            print(f"❌ Slack error: {response.status_code} — {response.text}")
            return False
    except requests.RequestException as e:
        print(f"❌ Slack request failed: {e}")
        return False
