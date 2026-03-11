"""Upload corrected examples to OpenAI and start a fine-tuning job.

Reads data/fine_tuning_ready.jsonl, uploads it via the OpenAI API, and creates
a fine-tuning job with gpt-4o-mini. Prints the job ID for tracking on platform.openai.com.
"""

import sys
from pathlib import Path

from openai import OpenAI

from app.core.config import settings


def _data_dir() -> Path:
    """Return the data directory from config (DATA_DIR env var)."""
    return Path(settings.data_dir)


def main() -> None:
    data_dir = _data_dir()
    input_path = data_dir / "fine_tuning_ready.jsonl"

    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        print("Run the correct script first to produce fine_tuning_ready.jsonl")
        sys.exit(1)

    client = OpenAI(api_key=settings.openai_api_key)

    with open(input_path, "rb") as f:
        file = client.files.create(file=f, purpose="fine-tune")

    job = client.fine_tuning.jobs.create(
        training_file=file.id,
        model="gpt-4o-mini-2024-07-18",
    )

    print(f"Uploaded file: {file.id}")
    print(f"Fine-tuning job ID: {job.id}")
    print("Track progress at: https://platform.openai.com")


if __name__ == "__main__":
    main()
