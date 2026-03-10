"""Collects review input/output pairs for OpenAI fine-tuning.

Appends each example to data/fine_tuning_examples.jsonl in the exact format
required by OpenAI fine-tuning API.
"""

import json
from pathlib import Path


def _data_dir() -> Path:
    """Return the data directory (backend/data), creating it if needed."""
    backend_root = Path(__file__).resolve().parent.parent.parent
    data_dir = backend_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def collect_review_example(
    system_prompt: str,
    user_message: str,
    review_output: str,
    *,
    output_path: Path | None = None,
) -> None:
    """Append one review example to the fine-tuning JSONL file.

    Args:
        system_prompt: The REVIEW_SYSTEM prompt with real values filled in.
        user_message: The REVIEW_HUMAN prompt with real values (code, language, standards).
        review_output: The final review text produced by the agent.
        output_path: Optional path to the JSONL file. Defaults to data/fine_tuning_examples.jsonl.
    """
    if output_path is None:
        output_path = _data_dir() / "fine_tuning_examples.jsonl"

    record = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": review_output},
        ]
    }
    line = json.dumps(record, ensure_ascii=False) + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "a", encoding="utf-8") as f:
        f.write(line)
