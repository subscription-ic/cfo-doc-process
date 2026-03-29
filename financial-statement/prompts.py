PROMPTS = {
    "v1": (
        "You will be given a PDF of financial results. Identify the main sections "
        "and write concise, expert-level summaries for each section. Include multiple sections "
        "(aim for 4-8 if the document supports it). Prioritize quantitative "
        "detail and material movements: revenue, NII/NIM, operating expenses, credit "
        "costs, asset quality (GNPA/NNPA), provisioning, capital ratios, liquidity, "
        "segment performance, and key drivers. Call out YoY/QoQ changes if stated, "
        "note any guidance or management commentary, and highlight risks. Return "
        "JSON only in this format: "
        '{"sections": [{"section": "...", "summary": "..."}]}. '
        "Do not include any extra keys or text."
    ),
    "v2": (
        "Objective: You are an expert document analysis system. You will be given the full "
        "content of a complete document. The document can belong to any domain. Your task is "
        "to identify multiple categories within the document and generate concise, meaningful "
        "summaries for each category. Return multiple items when the document supports it.\n\n"
        "Step 1 (internal only): Determine the type of content (table, narrative, mixed) and "
        "the purpose of the document (reporting, explanation, compliance, etc.). Do not include "
        "this reasoning in the output.\n\n"
        "Step 2: Classification. Primary category (select one): Financial Statements, "
        "Financial Performance, Segment Reporting, Operational Metrics, Business Overview, "
        "Management Commentary, Risk Factors, Product / Service Description, Market / Industry "
        "Analysis, Regulatory / Compliance, Legal / Disclosures, Notes to Accounts, Audit / "
        "Assurance Report, Tables / Data-heavy Page, Entity / Organizational Information, Other.\n\n"
        "Secondary tags (optional, up to 3): Table, Numerical Data, KPI Metrics, YoY / QoQ "
        "Comparison, Regulatory Reference, Audit Language, Technical Content, Legal Language, "
        "Definitions, Process Description.\n\n"
        "Step 3: Summary guidelines. Maximum 4-6 bullet points OR 4-5 lines per item. Focus on "
        "key insights, important numbers or metrics (if present), and significant observations. "
        "Avoid copying text directly or generic statements. Keep the summary concise, clear, "
        "and information-dense.\n\n"
        "Step 4: Key data extraction (if applicable). If the document contains structured or "
        "numerical data, extract key metrics such as revenue, profit, expenses, ratios (e.g., "
        "EPS, NPA, margins). If not applicable, return null.\n\n"
        "Step 5: Confidence level. Use: high (clear and structured document), medium (some "
        "ambiguity), low (unclear or mixed content).\n\n"
        "Return STRICT JSON only in this format: "
        '{"items":[{"primary_category":"<one category>","secondary_tags":["<tag1>","<tag2>"],'
        '"summary":"<concise summary>","key_entities":["<entity1>","<entity2>"],'
        '"key_metrics":{"revenue":"<value or null>","profit":"<value or null>",'
        '"expenses":"<value or null>","ratios":["<ratio1>","<ratio2>"]},'
        '"confidence":"<high | medium | low>"}]}.'
    ),
    "v3": (
        "Objective: Act as a high-precision financial document intelligence engine. You will "
        "be given the full content of a complete company document (financial results, annual "
        "report, regulatory filing). Your tasks are to classify the document based on its "
        "primary function, generate a high-signal summary, and extract key entities and "
        "financial metrics (if present). Return multiple items when the document supports "
        "multiple distinct functions or sections.\n\n"
        "Step 1 (internal only): Identify what the page is doing (reporting performance, "
        "segment breakdown, notes, disclosures, audit validation). If multiple elements exist, "
        "prioritize the dominant function. Do not output this reasoning.\n\n"
        "Step 2: Classification (mandatory). Primary category (select exactly one): Financial "
        "Results Statement, Segment Reporting, Financial Position, Notes to Financial Statements, "
        "Transaction / Event Disclosure, Audit / Review Report, Consolidated Financial Results, "
        "Consolidated Segment Reporting, Consolidated Financial Position, Regulatory / Accounting "
        "Disclosure, Entity Structure Information, Other.\n\n"
        "Secondary tags (optional, up to 3): Table, Numerical Data, Financial Metrics, Ratios, "
        "Narrative Text, Regulatory Reference, Audit Language.\n\n"
        "Step 3: Summary (critical). Maximum 4-5 bullet points OR 4 lines. Must include key "
        "financial metrics (revenue, profit, ratios, etc.) if present, important changes or "
        "disclosures, and business or analytical significance. Avoid copy-pasting and generic "
        "statements. Focus on numbers + meaning + insight.\n\n"
        "Step 4: Key extraction (mandatory). Key entities: extract only explicitly mentioned "
        "company names, business segments, subsidiaries, financial terms. Key metrics: always "
        "attempt extraction; if not present return null. Fields: revenue, profit, expenses, ratios "
        "(EPS, NPA, margins, etc.). Do not infer or calculate values.\n\n"
        "Step 5: Confidence. high (clear structure like financial tables/audit reports), medium "
        "(mixed content), low (ambiguous page).\n\n"
        "Return STRICT JSON only in this format: "
        '{"items":[{"primary_category":"<one category>","secondary_tags":["<tag1>","<tag2>"],'
        '"summary":"<concise high-signal summary>","key_entities":["<entity1>","<entity2>"],'
        '"key_metrics":{"revenue":"<value or null>","profit":"<value or null>",'
        '"expenses":"<value or null>","ratios":["<ratio1>","<ratio2>"]},'
        '"confidence":"<high | medium | low>"}]}.'
    ),
}

def get_prompt(version: str) -> str:
    if version not in PROMPTS:
        raise ValueError(f"Unknown prompt version: {version}")
    return PROMPTS[version]
