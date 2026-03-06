"""Unified CLI — dispatches to collect or send workflows.

Usage:
    python main.py collect --age-group 0-1          # Collect recommendations
    python main.py collect --age-group 3-5 --count 5
    python main.py send                             # Send to Slack
    python main.py send --dry-run                   # Preview
"""

import sys


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(
            "Daily Child Development Alert System\n"
            "\n"
            "Usage:\n"
            "  python main.py collect [options]    Workflow 1: Generate & save recommendations\n"
            "  python main.py send [options]       Workflow 2: Send a random unsent to Slack\n"
            "\n"
            "Run 'python main.py collect --help' or 'python main.py send --help' for details."
        )
        sys.exit(0)

    command = sys.argv[1]
    # Remove the subcommand from argv so argparse in the submodule works
    sys.argv = [sys.argv[0]] + sys.argv[2:]

    if command == "collect":
        from collect import main as collect_main
        collect_main()
    elif command == "send":
        from send import main as send_main
        send_main()
    else:
        print(f"❌ Unknown command: {command}. Use 'collect' or 'send'.")
        sys.exit(1)


if __name__ == "__main__":
    main()
