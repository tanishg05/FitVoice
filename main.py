"""FitVoice Command-Line Interface.

Run investigations, voice logs, or simple questions directly from the terminal.
"""

import argparse
import json
import sys
from fitvoice.orchestrator.runner import run_pipeline
from fitvoice.db.seed_data import seed_benchmark_data


def main():
    parser = argparse.ArgumentParser(description="FitVoice Genuine Multi-Agent AI System")
    parser.add_argument(
        "--query", "-q",
        type=str,
        default="Why has my bench press plateaued over the last 4 weeks despite working out consistently?",
        help="Inquiry or voice logging transcript"
    )
    parser.add_argument(
        "--user-id", "-u",
        type=str,
        default="alex_lifter",
        help="Target athlete identifier (default: 'alex_lifter')"
    )
    parser.add_argument(
        "--language", "-l",
        type=str,
        default="en-IN",
        help="Preferred language code (e.g., 'en-IN', 'hi-IN')"
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed or reset database with benchmark records before execution"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON state and execution trace"
    )

    args = parser.parse_args()

    if args.seed:
        print("🌱 Seeding reproducible benchmark dataset...")
        seed_benchmark_data()

    print(f"\n🚀 Running FitVoice Orchestrator for athlete '{args.user_id}'...")
    print(f"❓ Query: {args.query}\n")

    result = run_pipeline(
        user_query=args.query,
        user_id=args.user_id,
        preferred_language=args.language,
    )

    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return

    # Formatted terminal display
    print("=" * 70)
    print("📢 FINAL INTELLIGENCE RESPONSE:")
    print("=" * 70)
    print(result.get("final_response", "No response generated."))
    print("=" * 70)

    print("\n🕵️ OBSERVABLE AGENT EXECUTION TRACE:")
    print("-" * 70)
    for evt in result.get("agent_execution_trace", []):
        v = evt.get("validation_status", "N/A")
        print(f"[{evt['agent_name']}] -> {evt['stage']} | Status: {evt['status']} | Validation: {v} | Duration: {evt['duration_ms']}ms")
        print(f"   Task: {evt['task_assigned']}")
        print(f"   Summary: {evt['result_summary']}")
        print("-" * 70)


if __name__ == "__main__":
    main()
