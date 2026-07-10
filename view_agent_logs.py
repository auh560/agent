from typing import Any

from agent_run_store import load_agent_runs


def print_log_summary(record: dict[str, Any], index: int) -> None:
    result = record.get("result", {})
    state = result.get("state", {})
    steps = state.get("steps", [])
    errors = state.get("errors", [])

    print(f"\nRun #{index}")
    print(f"run_id: {record.get('run_id')}")
    print(f"created_at: {record.get('created_at')}")
    print(f"user_message: {record.get('user_message')}")
    print(f"answer: {result.get('answer')}")
    print(f"steps: {len(steps)}")
    print(f"errors: {len(errors)}")

    if errors:
        print("error_details:")
        for error in errors:
            print(f"- step={error.get('step')} error={error.get('error')}")


def main() -> int:
    records = load_agent_runs()
    if not records:
        print("No agent logs found.")
        return 0

    for index, record in enumerate(records, start=1):
        print_log_summary(record, index)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
