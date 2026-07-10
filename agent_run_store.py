import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


AGENT_RUN_LOG_PATH = Path("logs") / "agent_runs.jsonl"


def generate_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    suffix = uuid4().hex[:8]
    return f"run_{timestamp}_{suffix}"


def save_agent_run(run_id: str, user_message: str, result: Any) -> None:
    AGENT_RUN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "user_message": user_message,
        "result": result.model_dump(),
    }
    with AGENT_RUN_LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_agent_runs(log_path: Path = AGENT_RUN_LOG_PATH) -> list[dict[str, Any]]:
    if not log_path.exists():
        return []

    records: list[dict[str, Any]] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))

    return records


def find_agent_run(run_id: str) -> dict[str, Any] | None:
    for record in load_agent_runs():
        if record.get("run_id") == run_id:
            return record

    return None
