# Predict Script README

This document explains how to run `predict_questions.py`, what inputs it expects, and what outputs it creates.

## What This Script Does

`predict_questions.py`:
- Reads historical transcript and financial statement data listed in `input-map.xlsx`
- Uploads the current quarter financial-results PDF
- Calls OpenAI in two separate requests:
  - Predicted analyst questions
  - Predicted analyst topics
- Writes one value per row (cell-by-cell) in two Excel output files

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

## Required Files and Paths

- Script: `predict_questions.py`
- Input map file: `input-map.xlsx`
- Input folder: `inputs/`
- Environment file: `.env` (or system env var)

### 1) Configure Financial PDF Path

Edit this variable in `predict_questions.py`:

```python
FIN_PDF_PATH = r"C:\path\to\financial_results.pdf"
```

### 2) Configure Input Map

`input-map.xlsx` must include these columns (exact names expected):
- `QTR`
- `transcript`
- `fin-statement`

For each row:
- `transcript` should be a filename present in `inputs/`
- `fin-statement` should be a filename present in `inputs/`

### 3) Configure API Key

Option A: use `.env` in the same folder:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

Option B: set environment variable in terminal session:

```powershell
$env:OPENAI_API_KEY="your_openai_api_key_here"
```

## How to Run

From the `predict` folder:

```powershell
python predict_questions.py
```

If you want to force your global Python executable:

```powershell
& C:\Users\shiv\AppData\Local\Programs\Python\Python310\python.exe predict_questions.py
```

## Checkpoint Logs You Will See

The script prints progress checkpoints like:
- `[checkpoint] 1/9 Starting predict_questions.py`
- `[checkpoint] 5/9 Uploaded financial PDF; file_id=...`
- `[checkpoint] 9/9 Wrote outputs/predicted_topics.xlsx`
- `[checkpoint] Done`

## Outputs

Generated in `outputs/`:

1. `predicted_questions.xlsx`
   - Column: `predicted_question`
   - One predicted question per row

2. `predicted_topics.xlsx`
   - Column: `predicted_topic`
   - One predicted topic per row

## Common Errors

- `Missing OPENAI_API_KEY environment variable.`
  - Fix: set `OPENAI_API_KEY` in `.env` or terminal env

- `PDF not found at: ...`
  - Fix: correct `FIN_PDF_PATH`

- `Input file not found` / missing Excel files
  - Fix: verify `input-map.xlsx` and files in `inputs/`

- OpenAI 400 model error
  - Fix: set valid `OPENAI_MODEL` in `.env`, for example `gpt-4.1-mini`
