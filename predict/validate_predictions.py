import json
import mimetypes
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

# Paste transcript PDF path here.
TRANSCRIPT_PDF_PATH = r"C:\Users\shiv\Desktop\ic\cfo\docs\HDFC\Transcript\HDFCB_Q3FY26_Transcript_Final.pdf"

# Input prediction files.
PREDICTED_QUESTIONS_PATH = Path("outputs/predicted_questions.xlsx")
PREDICTED_TOPICS_PATH = Path("outputs/predicted_topics.xlsx")

# Output validation files.
OUTPUT_DIR = Path("outputs")
QUESTION_VALIDATION_OUTPUT = OUTPUT_DIR / "question_validation.xlsx"
TOPIC_VALIDATION_OUTPUT = OUTPUT_DIR / "topic_validation.xlsx"

LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini"


def load_openai_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        return api_key

    env_path = Path(".env")
    if env_path.exists():
        with env_path.open("r", encoding="utf-8") as env_file:
            for line in env_file:
                text = line.strip()
                if not text or text.startswith("#") or "=" not in text:
                    continue
                key, value = text.split("=", 1)
                if key.strip() == "OPENAI_API_KEY":
                    return value.strip().strip('"').strip("'")
    return ""


LLM_API_KEY = load_openai_api_key()


def build_multipart_form_data(fields: Dict[str, str], file_path: str) -> bytes:
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    line_break = "\r\n"
    file_name = Path(file_path).name
    content_type = mimetypes.guess_type(file_name)[0] or "application/pdf"

    parts: List[bytes] = []
    for name, value in fields.items():
        parts.append(f"--{boundary}{line_break}".encode("utf-8"))
        parts.append(
            f'Content-Disposition: form-data; name="{name}"{line_break}{line_break}'.encode(
                "utf-8"
            )
        )
        parts.append(f"{value}{line_break}".encode("utf-8"))

    parts.append(f"--{boundary}{line_break}".encode("utf-8"))
    parts.append(
        f'Content-Disposition: form-data; name="file"; filename="{file_name}"{line_break}'.encode(
            "utf-8"
        )
    )
    parts.append(f"Content-Type: {content_type}{line_break}{line_break}".encode("utf-8"))
    with open(file_path, "rb") as file_handle:
        parts.append(file_handle.read())
    parts.append(line_break.encode("utf-8"))

    parts.append(f"--{boundary}--{line_break}".encode("utf-8"))
    return b"".join(parts)


def upload_pdf_to_openai(pdf_path: str) -> str:
    if not pdf_path:
        raise ValueError("TRANSCRIPT_PDF_PATH is required.")
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"PDF not found at: {pdf_path}")
    if not LLM_API_KEY:
        raise ValueError("Missing OPENAI_API_KEY environment variable.")

    fields = {"purpose": "assistants"}
    body = build_multipart_form_data(fields, pdf_path)
    content_type = "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW"

    request = urllib.request.Request(
        "https://api.openai.com/v1/files",
        data=body,
        headers={
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": content_type,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request) as response:
            response_json = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"File upload failed: {exc.code} {exc.reason}: {detail}")

    file_id = response_json.get("id") if isinstance(response_json, dict) else None
    if not file_id:
        raise RuntimeError("File upload failed: missing file id in response.")
    return str(file_id)


def extract_response_text(response_json: Dict[str, Any]) -> str:
    if isinstance(response_json, dict) and response_json.get("output_text"):
        return str(response_json.get("output_text"))
    output_items = response_json.get("output", []) if isinstance(response_json, dict) else []
    texts: List[str] = []
    for item in output_items:
        for content in item.get("content", []) if isinstance(item, dict) else []:
            if content.get("type") == "output_text" and content.get("text"):
                texts.append(str(content.get("text")))
    return "\n".join(texts).strip()


def call_llm(prompt: str, pdf_file_id: str) -> str:
    if not LLM_API_KEY:
        raise ValueError("Missing OPENAI_API_KEY environment variable.")

    payload = {
        "model": LLM_MODEL,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_file", "file_id": pdf_file_id},
                ],
            }
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=data,
        headers={
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request) as response:
            response_json = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"LLM request failed: {exc.code} {exc.reason}: {detail}")

    return extract_response_text(response_json)


def parse_json_array(text: str) -> List[Dict[str, Any]]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return []

    if isinstance(parsed, list):
        items: List[Dict[str, Any]] = []
        for row in parsed:
            if isinstance(row, dict):
                items.append(row)
        return items
    return []


def load_prediction_column(excel_path: Path, preferred_column: str) -> List[str]:
    if not excel_path.exists():
        raise FileNotFoundError(f"Input file not found: {excel_path}")

    df = pd.read_excel(excel_path)
    if df.empty:
        return []

    columns = {str(c).strip().lower(): c for c in df.columns}
    selected_col = columns.get(preferred_column.lower())
    if selected_col is None:
        selected_col = list(df.columns)[0]

    values: List[str] = []
    for value in df[selected_col].fillna("").tolist():
        text = str(value).strip()
        if text:
            values.append(text)
    return values


def normalize_validation_rows(
    source_items: List[str],
    model_rows: List[Dict[str, Any]],
    item_key: str,
) -> List[Dict[str, str]]:
    by_item: Dict[str, Dict[str, Any]] = {}
    for row in model_rows:
        item = str(row.get(item_key, "")).strip()
        if item:
            by_item[item] = row

    output_rows: List[Dict[str, str]] = []
    for item in source_items:
        row = by_item.get(item, {})
        asked_value = str(row.get("asked_in_transcript", "No")).strip().lower()
        asked = "Yes" if asked_value == "yes" else "No"

        confidence_value = str(row.get("confidence", "Medium")).strip().lower()
        if confidence_value in {"high", "medium", "low"}:
            confidence = confidence_value.capitalize()
        else:
            confidence = "Medium"

        reason = str(row.get("reason", "")).strip()
        if not reason:
            reason = "No structured reason returned by model."

        output_rows.append(
            {
                item_key: item,
                "asked_in_transcript": asked,
                "confidence": confidence,
                "reason": reason,
            }
        )

    return output_rows


def build_topic_validation_prompt(topics: List[str]) -> str:
    return (
        "You are validating whether predicted analyst topics were asked in the attached "
        "earnings call transcript PDF.\n"
        "For each topic, return whether it was asked in the transcript.\n"
        "Return strict JSON only as an array of objects with keys: "
        "predicted_topic, asked_in_transcript, confidence, reason.\n"
        "Rules:\n"
        "- asked_in_transcript must be exactly Yes or No.\n"
        "- confidence must be High, Medium, or Low.\n"
        "- reason must be concise and specific to transcript evidence.\n"
        "- Include one object for each topic provided; do not skip items.\n\n"
        f"Predicted topics JSON:\n{json.dumps(topics, ensure_ascii=False)}"
    )


def build_question_validation_prompt(questions: List[str]) -> str:
    return (
        "You are validating whether predicted analyst questions were asked in the attached "
        "earnings call transcript PDF.\n"
        "For each predicted question, return whether it was asked in the transcript.\n"
        "Return strict JSON only as an array of objects with keys: "
        "predicted_question, asked_in_transcript, confidence, reason.\n"
        "Rules:\n"
        "- asked_in_transcript must be exactly Yes or No.\n"
        "- confidence must be High, Medium, or Low.\n"
        "- reason must be concise and specific to transcript evidence.\n"
        "- Include one object for each question provided; do not skip items.\n\n"
        f"Predicted questions JSON:\n{json.dumps(questions, ensure_ascii=False)}"
    )


def main() -> None:
    print("[checkpoint] 1/10 Starting validate_predictions.py")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[checkpoint] 2/10 Ensured output directory: {OUTPUT_DIR}")

    predicted_questions = load_prediction_column(PREDICTED_QUESTIONS_PATH, "predicted_question")
    predicted_topics = load_prediction_column(PREDICTED_TOPICS_PATH, "predicted_topic")
    print(
        f"[checkpoint] 3/10 Loaded predictions: questions={len(predicted_questions)}, topics={len(predicted_topics)}"
    )

    if not predicted_questions:
        raise ValueError("No predicted questions found in input Excel.")
    if not predicted_topics:
        raise ValueError("No predicted topics found in input Excel.")

    pdf_file_id = upload_pdf_to_openai(TRANSCRIPT_PDF_PATH)
    print(f"[checkpoint] 4/10 Uploaded transcript PDF; file_id={pdf_file_id}")

    topic_prompt = build_topic_validation_prompt(predicted_topics)
    print("[checkpoint] 5/10 Sending topic validation request")
    topic_response_text = call_llm(topic_prompt, pdf_file_id)
    print("[checkpoint] 6/10 Received topic validation response")
    topic_rows_raw = parse_json_array(topic_response_text)
    topic_rows = normalize_validation_rows(
        source_items=predicted_topics,
        model_rows=topic_rows_raw,
        item_key="predicted_topic",
    )
    print(f"[checkpoint] 7/10 Normalized topic validations: rows={len(topic_rows)}")

    question_prompt = build_question_validation_prompt(predicted_questions)
    print("[checkpoint] 8/10 Sending question validation request")
    question_response_text = call_llm(question_prompt, pdf_file_id)
    print("[checkpoint] 8/10 Received question validation response")
    question_rows_raw = parse_json_array(question_response_text)
    question_rows = normalize_validation_rows(
        source_items=predicted_questions,
        model_rows=question_rows_raw,
        item_key="predicted_question",
    )
    print(f"[checkpoint] 9/10 Normalized question validations: rows={len(question_rows)}")

    topic_df = pd.DataFrame(
        topic_rows,
        columns=["predicted_topic", "asked_in_transcript", "confidence", "reason"],
    )
    topic_df.to_excel(TOPIC_VALIDATION_OUTPUT, index=False)

    question_df = pd.DataFrame(
        question_rows,
        columns=["predicted_question", "asked_in_transcript", "confidence", "reason"],
    )
    question_df.to_excel(QUESTION_VALIDATION_OUTPUT, index=False)
    print(
        f"[checkpoint] 10/10 Wrote outputs: {TOPIC_VALIDATION_OUTPUT.name}, {QUESTION_VALIDATION_OUTPUT.name}"
    )
    print("[checkpoint] Done")


if __name__ == "__main__":
    main()
