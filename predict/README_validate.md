# Validate Script README

This document explains how to run `validate_predictions.py`, what inputs it expects, and what outputs it creates.

## What This Script Does

`validate_predictions.py`:
- Reads predicted topics and predicted questions from Excel files in `outputs/`
- Uploads a transcript PDF
- Sends two separate OpenAI validation calls:
  - Topics + transcript PDF
  - Questions + transcript PDF
- Returns for each item:
  - Yes/No whether it was asked
  - Confidence
  - Reason
- Writes two validation Excel outputs

## Prerequisites

- Python 3.10+
- Packages:
  - pandas
  - openpyxl
- OpenAI API key

Install dependencies:

```powershell
pip install pandas openpyxl
```

## Required Inputs

- Script: `validate_predictions.py`
- Predicted questions file: `outputs/predicted_questions.xlsx`
- Predicted topics file: `outputs/predicted_topics.xlsx`
- Transcript PDF path configured in script
- `.env` (or system env var) with API key

### 1) Configure Transcript PDF Path

Edit this variable in `validate_predictions.py`:

```python
TRANSCRIPT_PDF_PATH = r"C:\path\to\transcript.pdf"
```

### 2) Input File Formats

`outputs/predicted_questions.xlsx`:
- Preferred column name: `predicted_question`
- If missing, script falls back to first column

`outputs/predicted_topics.xlsx`:
- Preferred column name: `predicted_topic`
- If missing, script falls back to first column

### 3) Configure API Key

Option A: `.env` file in same folder:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

Option B: set in terminal session:

```powershell
$env:OPENAI_API_KEY="your_openai_api_key_here"
```

## How to Run

From the `predict` folder:

```powershell
python validate_predictions.py
```

Or force global Python:

```powershell
& C:\Users\shiv\AppData\Local\Programs\Python\Python310\python.exe validate_predictions.py
```

## Checkpoint Logs You Will See

The script prints checkpoints such as:
- `[checkpoint] 1/10 Starting validate_predictions.py`
- `[checkpoint] 4/10 Uploaded transcript PDF; file_id=...`
- `[checkpoint] 7/10 Normalized topic validations: rows=...`
- `[checkpoint] 10/10 Wrote outputs: topic_validation.xlsx, question_validation.xlsx`
- `[checkpoint] Done`

## Outputs

Generated in `outputs/`:

1. `topic_validation.xlsx`
   - Columns:
     - `predicted_topic`
     - `asked_in_transcript` (Yes/No)
     - `confidence` (High/Medium/Low)
     - `reason`

2. `question_validation.xlsx`
   - Columns:
     - `predicted_question`
     - `asked_in_transcript` (Yes/No)
     - `confidence` (High/Medium/Low)
     - `reason`

## Common Errors

- `No predicted questions found in input Excel.`
  - Fix: ensure `outputs/predicted_questions.xlsx` exists and has rows

- `No predicted topics found in input Excel.`
  - Fix: ensure `outputs/predicted_topics.xlsx` exists and has rows

- `PDF not found at: ...`
  - Fix: correct `TRANSCRIPT_PDF_PATH`

- `Missing OPENAI_API_KEY environment variable.`
  - Fix: set key in `.env` or terminal environment
