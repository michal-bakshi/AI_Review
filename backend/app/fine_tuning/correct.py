"""Interactive script to correct review examples before fine-tuning.

Loads data/fine_tuning_examples.jsonl, lets the user mark each example as
correct or edit the assistant content, then writes data/fine_tuning_ready.jsonl.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from app.core.config import settings


def _data_dir() -> Path:
    """Return the data directory from config (DATA_DIR env var)."""
    return Path(settings.data_dir)


def _edit_in_editor(content: str) -> str:
    """Open content in the user's editor and return the edited text."""
    editor = os.environ.get("EDITOR")
    if editor is None and sys.platform == "win32":
        editor = "notepad"
    if editor is None:
        editor = "nano"

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".md",
        delete=False,
        encoding="utf-8",
    ) as f:
        f.write(content)
        path = f.name

    try:
        subprocess.run([editor, path], check=True)
        return Path(path).read_text(encoding="utf-8")
    finally:
        Path(path).unlink(missing_ok=True)


def main() -> None:
    data_dir = _data_dir()
    input_path = data_dir / "fine_tuning_examples.jsonl"
    output_path = data_dir / "fine_tuning_ready.jsonl"

    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        print("Run the review pipeline first (submit code for review) so examples are collected.")
        sys.exit(1)

    examples: list[dict] = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            examples.append(json.loads(line))

    if not examples:
        print("No examples in input file.")
        sys.exit(0)

    corrected: list[dict] = []
    for i, record in enumerate(examples):
        messages = record["messages"]
        system_content = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_content = next((m["content"] for m in messages if m["role"] == "user"), "")
        assistant_content = next((m["content"] for m in messages if m["role"] == "assistant"), "")

        print("\n" + "=" * 60)
        print(f"Example {i + 1} / {len(examples)}")
        print("=" * 60)
        print("\n[System]")
        print(system_content[:500] + ("..." if len(system_content) > 500 else ""))
        print("\n[User]")
        print(user_content[:500] + ("..." if len(user_content) > 500 else ""))
        print("\n[Assistant]")
        print(assistant_content)
        print()

        while True:
            answer = input("Is this review correct? (y/n): ").strip().lower()
            if answer == "y":
                corrected.append(record)
                break
            if answer == "n":
                new_assistant = _edit_in_editor(assistant_content)
                updated = {
                    "messages": [
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": user_content},
                        {"role": "assistant", "content": new_assistant},
                    ]
                }
                corrected.append(updated)
                break
            print("Please enter y or n.")

    data_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for record in corrected:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\nSaved {len(corrected)} examples to {output_path}")


if __name__ == "__main__":
    main()
