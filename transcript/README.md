# Transcript Q&A Extraction

This folder contains a page-wise LLM pipeline to extract Q&A from earnings-call PDFs and save a single-sheet Excel file.

## Script

- `extract_qa_llm_pagewise.py`

## Output Columns

- `question`
- `person`
- `answer`
- `question category`
- `question sub topic`
- `reason`

## Prerequisites

- Python 3.10+
- OpenAI API key

Install dependencies:

```powershell
pip install openai openpyxl pypdf
```

## Environment Setup

Create or update `transcript/.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

The script loads `.env` from the current working directory, so run from the `transcript` folder (or pass `--api-key-env` with a variable available in your shell).

## How To Run

From repo root:

```powershell
cd <repo-root>\transcript
```

Run for a single PDF:

```powershell
python extract_qa_llm_pagewise.py --input "..\pdf\transcript---q3-fy24--earnings-call.pdf" --output-dir "..\qna-excel" --delay 0 --suffix=qa-llm
```

Run for all PDFs in a folder:

```powershell
python extract_qa_llm_pagewise.py --input "..\pdf" --output-dir "..\qna-excel" --delay 0 --suffix=qa-llm
```

## Important Notes

- `--delay` is seconds between API calls. Example: `0`, `0.2`, `0.5`.
- If suffix starts with `-`, pass it using equals form, for example `--suffix=-qa-llm`.
- Output filename pattern is `<pdf_stem><suffix>.xlsx`.
  - Example: `transcript---q3-fy24--earnings-callqa-llm.xlsx` (for `--suffix=qa-llm`)
  - Example: `transcript---q3-fy24--earnings-call-qa-llm.xlsx` (for `--suffix=-qa-llm`)

## Optional Arguments

- `--sheet` default: `QA`
- `--extract-model` default: `gpt-4o-mini`
- `--classify-model` default: `gpt-4o-mini`
- `--api-key-env` default: `OPENAI_API_KEY`
