import json
import os
import mimetypes
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

# TODO: Set this to the financial results PDF you want to use for predictions.
FIN_PDF_PATH = r"C:\Users\shiv\Desktop\ic\cfo\docs\HDFC\Financial Results\q3fy26.pdf"

# Input map file that lists quarter, transcript file, and fin-statement file.
INPUT_MAP_PATH = Path("input-map.xlsx")

# Output directory for predictions.
OUTPUT_DIR = Path("outputs")

# LLM configuration (reads API key/model from environment).
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
            f'Content-Disposition: form-data; name="{name}"{line_break}{line_break}'
            .encode("utf-8")
        )
        parts.append(f"{value}{line_break}".encode("utf-8"))

    parts.append(f"--{boundary}{line_break}".encode("utf-8"))
    parts.append(
        f'Content-Disposition: form-data; name="file"; filename="{file_name}"{line_break}'
        .encode("utf-8")
    )
    parts.append(f"Content-Type: {content_type}{line_break}{line_break}".encode("utf-8"))
    with open(file_path, "rb") as file_handle:
        parts.append(file_handle.read())
    parts.append(line_break.encode("utf-8"))

    parts.append(f"--{boundary}--{line_break}".encode("utf-8"))
    return b"".join(parts)


def upload_pdf_to_openai(pdf_path: str) -> str:
    if not pdf_path:
        raise ValueError("FIN_PDF_PATH is required.")
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


def read_transcript_excel(path: Path) -> List[Dict[str, Any]]:
    df = pd.read_excel(path)
    # Expecting columns: question, answer, theme (case-insensitive).
    df.columns = [c.strip().lower() for c in df.columns]
    keep = [c for c in ["question", "answer", "theme"] if c in df.columns]
    return df[keep].fillna("").to_dict(orient="records")


def read_fin_statement_excel(path: Path) -> List[Dict[str, Any]]:
    df = pd.read_excel(path)
    return df.fillna("").to_dict(orient="records")


def build_payload(input_map: pd.DataFrame) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    for _, row in input_map.iterrows():
        qtr = str(row["QTR"]).strip()
        transcript_path = Path("inputs") / str(row["transcript"]).strip()
        fin_path = Path("inputs") / str(row["fin-statement"]).strip()

        payload[qtr] = {
            "transcript": read_transcript_excel(transcript_path),
            "fin_statement": read_fin_statement_excel(fin_path),
        }
    return payload


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


def parse_llm_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def predictions_to_rows(predictions_json: Any, raw_text: str, kind: str) -> List[str]:
    rows: List[str] = []

    if isinstance(predictions_json, list):
        for item in predictions_json:
            if isinstance(item, str):
                value = item.strip()
                if value:
                    rows.append(value)
            elif isinstance(item, dict):
                # Try common keys first, then fall back to JSON for object-shaped rows.
                keys = ["question", "topic", "text", "title", "name"]
                chosen = ""
                for key in keys:
                    val = item.get(key)
                    if isinstance(val, str) and val.strip():
                        chosen = val.strip()
                        break
                if chosen:
                    rows.append(chosen)
                else:
                    rows.append(json.dumps(item, ensure_ascii=False))
            elif item is not None:
                rows.append(str(item).strip())

    if rows:
        return rows

    # Fallback when model doesn't return valid JSON: split non-empty lines.
    for line in (raw_text or "").splitlines():
        value = line.strip().lstrip("-•0123456789. ").strip()
        if value:
            rows.append(value)

    # Ensure file has a predictable header even if model returns nothing.
    if not rows:
        return [""]

    return rows


def main() -> None:
    print("[checkpoint] 1/9 Starting predict_questions.py")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[checkpoint] 2/9 Ensured output directory: {OUTPUT_DIR}")

    input_map = pd.read_excel(INPUT_MAP_PATH)
    print(f"[checkpoint] 3/9 Loaded input map: {INPUT_MAP_PATH} (rows={len(input_map)})")
    # Normalize column names to match the input-map screenshot.
    input_map.columns = [c.strip() for c in input_map.columns]

    payload = build_payload(input_map)
    print("[checkpoint] 4/9 Built historical payload from inputs")
    pdf_file_id = upload_pdf_to_openai(FIN_PDF_PATH)
    print(f"[checkpoint] 5/9 Uploaded financial PDF; file_id={pdf_file_id}")

    # Prediction 1: questions
    questions_prompt = (
        "You are given past quarters' transcripts and financial statement tables, "
        "plus the current quarter's financial results PDF text. "
        "Predict the questions that analysts will ask next. "
        "Return JSON only (an array of questions or objects).\n\n"
        "The financial results PDF is attached as a file.\n\n"
        f"Historical data JSON:\n{json.dumps(payload)}"
    )
    print("[checkpoint] 6/9 Sending questions prediction request")
    questions_response = call_llm(questions_prompt, pdf_file_id)
    questions_json = parse_llm_json(questions_response)
    print("[checkpoint] 6/9 Received questions prediction response")

    # Prediction 2: topics
    topics_prompt = (
        "You are given past quarters' transcripts and financial statement tables, "
        "plus the current quarter's financial results PDF text. "
        "Predict the topics of questions that analysts will ask next. "
        "Return JSON only (an array of topic strings or objects).\n\n"
        "The financial results PDF is attached as a file.\n\n"
        f"Historical data JSON:\n{json.dumps(payload)}"
    )
    print("[checkpoint] 7/9 Sending topics prediction request")
    topics_response = call_llm(topics_prompt, pdf_file_id)
    topics_json = parse_llm_json(topics_response)
    print("[checkpoint] 7/9 Received topics prediction response")

    # Save outputs as one prediction per row (cell-by-cell).
    questions_rows = predictions_to_rows(questions_json, questions_response, "question")
    questions_df = pd.DataFrame({"predicted_question": questions_rows})
    questions_df.to_excel(OUTPUT_DIR / "predicted_questions.xlsx", index=False)

    print("[checkpoint] 8/9 Wrote outputs/predicted_questions.xlsx")
    topics_rows = predictions_to_rows(topics_json, topics_response, "topic")
    topics_df = pd.DataFrame({"predicted_topic": topics_rows})
    topics_df.to_excel(OUTPUT_DIR / "predicted_topics.xlsx", index=False)

    print("[checkpoint] 9/9 Wrote outputs/predicted_topics.xlsx")
    print("[checkpoint] Done")

if __name__ == "__main__":
    main()
