# Financial Statement Extraction

## IMPORTANT

- Name input PDF files in this format: `q4fy24.pdf`

This folder contains a script to extract structured section summaries from HDFC financial results PDFs.

## Script

- `extract_hdfc_fin_results_sections.py`

## What It Does

- Reads all PDF files from `C:\Users\shiv\Desktop\ic\cfo\pdf` ( change this to your input folder)
- Sends each PDF to OpenAI with a versioned prompt
- Parses and validates JSON-like output
- Saves one Excel file per input PDF under the `op` folder

## Prerequisites

- Python 3.10+
- OpenAI API key

Install dependencies from repo root:

```powershell
pip install openai pandas python-dotenv pydantic
```

## Environment Setup

Create or update `financial-statement/.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

## How To Run

From repo root (`C:\Users\..\cfo-doc-process`):

```powershell
python .\financial-statement\extract_hdfc_fin_results_sections.py --version v3
```

You can change the prompt/model version:

```powershell
python .\financial-statement\extract_hdfc_fin_results_sections.py --version v1
```

## Output

- Output folder: `op`
- Output file pattern: `<input_pdf_name>_fin_summary_prompt2.xlsx`

Example:

- Input: `hdfc-q3fy24.pdf`
- Output: `op\hdfc-q3fy24_fin_summary_prompt2.xlsx`

## Notes

- Input directory is currently hardcoded in the script as:
  - `INPUT_DIR = C:\Users\shiv\Desktop\ic\cfo\pdf`
- If there are no PDFs in that folder, no output files will be generated.
