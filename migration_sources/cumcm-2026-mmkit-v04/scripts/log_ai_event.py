import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Append one non-secret AI-use event to a competition workspace.")
    p.add_argument("--workspace", required=True)
    p.add_argument("--backend", required=True)
    p.add_argument("--model", default="")
    p.add_argument("--task", required=True)
    p.add_argument("--result", default="")
    p.add_argument("--output-ref", default="")
    p.add_argument("--notes", default="")
    args = p.parse_args()

    workspace = Path(args.workspace).resolve()
    log_dir = workspace / "08_ai_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / "ai_calls.jsonl"

    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "backend": args.backend,
        "model": args.model,
        "task": args.task,
        "result": args.result,
        "output_ref": args.output_ref,
        "notes": args.notes,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(path)


if __name__ == "__main__":
    main()
