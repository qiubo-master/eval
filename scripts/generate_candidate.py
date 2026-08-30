"""Call a candidate deployment and materialize its outputs into a versioned eval dataset."""

import argparse
import json
import urllib.request
from pathlib import Path


def generate(api_base_url: str, source: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with source.open(encoding="utf-8") as src, output.open("w", encoding="utf-8") as dst:
        for line in src:
            if not line.strip():
                continue
            row = json.loads(line)
            payload = json.dumps({
                "user_id": f"offline-{row['id']}",
                "session_id": "offline-eval",
                "scenario": row["scenario"],
                "message": row["input"],
                "contexts": row["retrieval_context"],
            }).encode()
            request = urllib.request.Request(
                f"{api_base_url.rstrip('/')}/v1/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                result = json.loads(response.read())
            row["actual_output"] = result["answer"]
            row["candidate_metadata"] = {
                "model": result["model"],
                "variant": result["variant"],
                "trace_id": result["trace_id"],
            }
            dst.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--api-base-url", default="http://localhost:8000")
    args = parser.parse_args()
    generate(args.api_base_url, args.source, args.output)


if __name__ == "__main__":
    main()

