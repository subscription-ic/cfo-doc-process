import argparse
import json
import os
import re

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError

from op.models import (
    get_output_columns,
    get_response_model,
    model_to_rows,
    validate_response,
)
from op.prompts import get_prompt

# Usage:
# 1) pip install openai pandas python-dotenv
# 2) Ensure OPENAI_API_KEY is set in your .env
# 3) python -m op.extract_hdfc_fin_results_sections --version v1

INPUT_DIR = r"C:\Users\shiv\Desktop\ic\cfo\pdf"
OUTPUT_DIR = "op"
OUTPUT_SUFFIX = "_fin_summary_prompt2.xlsx"
MODEL_NAME = "gpt-5.4"


def parse_report_meta(filename: str) -> tuple[str, str]:
    name = os.path.splitext(os.path.basename(filename))[0]
    name_lower = name.lower()

    year = "unknown"
    year_match = re.search(r"(20\d{2})", name_lower)
    if year_match:
        year = year_match.group(1)
    else:
        fy_match = re.search(r"fy\s?(\d{2})", name_lower)
        if fy_match:
            year = f"20{fy_match.group(1)}"

    quarter = "unknown"
    q_match = re.search(r"q([1-4])", name_lower, re.IGNORECASE)
    if q_match:
        quarter = f"Q{q_match.group(1)}"
    else:
        if re.search(r"\bfirst\s+quarter\b|\bquarter\s+1\b|\bQ1\b", name, re.IGNORECASE):
            quarter = "Q1"
        elif re.search(r"\bsecond\s+quarter\b|\bquarter\s+2\b|\bQ2\b", name, re.IGNORECASE):
            quarter = "Q2"
        elif re.search(r"\bthird\s+quarter\b|\bquarter\s+3\b|\bQ3\b", name, re.IGNORECASE):
            quarter = "Q3"
        elif re.search(r"\bfourth\s+quarter\b|\bquarter\s+4\b|\bQ4\b", name, re.IGNORECASE):
            quarter = "Q4"

    return year, quarter


def summarize_pdf_sections(
    client: OpenAI,
    pdf_path: str,
    prompt_version: str,
    model_version: str,
) -> list[dict[str, object]]:
    prompt = get_prompt(prompt_version)

    with open(pdf_path, "rb") as pdf_file:
        uploaded = client.files.create(file=pdf_file, purpose="assistants")

    response = client.responses.create(
        model=MODEL_NAME,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_file", "file_id": uploaded.id},
                ],
            }
        ],
        temperature=0.2,
        max_output_tokens=12000,
    )

    output_text = getattr(response, "output_text", "") or ""
    if not output_text:
        try:
            output_text = response.output[0].content[0].text
        except (AttributeError, IndexError, KeyError, TypeError):
            output_text = ""

    print("LLM output (raw):")
    print(output_text)

    # Best-effort JSON extraction if the model adds extra wrapping text.
    cleaned = output_text.strip()
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    json_candidate = cleaned
    if "{" in cleaned and "}" in cleaned:
        json_candidate = cleaned[cleaned.find("{") : cleaned.rfind("}") + 1]

    try:
        parsed = json.loads(json_candidate)
        model_cls = get_response_model(model_version)
        validated = validate_response(model_cls, parsed)
        return model_to_rows(model_version, validated, fallback_text="")
    except (json.JSONDecodeError, ValidationError, ValueError, AttributeError):
        return model_to_rows(model_version, None, fallback_text=output_text.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract section summaries from HDFC financial results PDFs."
    )
    parser.add_argument(
        "--version",
        default="v1",
        help="Prompt/model version to use.",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    client = OpenAI()

    args = parse_args()
    version = args.version

    input_dir = os.path.join(os.getcwd(), INPUT_DIR)
    output_dir = os.path.join(os.getcwd(), OUTPUT_DIR)
    os.makedirs(output_dir, exist_ok=True)

    pdf_files = [
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if f.lower().endswith(".pdf")
    ]

    for pdf_path in pdf_files:
        print(f"Processing {os.path.basename(pdf_path)}...")
        year, quarter = parse_report_meta(pdf_path)
        sections = summarize_pdf_sections(
            client,
            pdf_path,
            prompt_version=version,
            model_version=version,
        )

        rows = []
        for item in sections:
            row = {
                "file": os.path.basename(pdf_path),
                "year": year,
                "quarter": quarter,
            }
            row.update(item)
            rows.append(row)

        if not rows:
            print("No content found to summarize.")
            continue

        df = pd.DataFrame(rows)
        ordered_columns = ["file", "year", "quarter"] + get_output_columns(version)
        df = df.reindex(columns=ordered_columns)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_name = f"{base_name}{OUTPUT_SUFFIX}"
        output_path = os.path.join(output_dir, output_name)
        df.to_excel(output_path, index=False)
        print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
