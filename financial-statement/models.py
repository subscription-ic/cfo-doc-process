from typing import Optional

from pydantic import BaseModel


class SectionSummaryV1(BaseModel):
    section: str
    summary: str


class SummaryResponseV1(BaseModel):
    sections: list[SectionSummaryV1]


class KeyMetricsV2(BaseModel):
    revenue: Optional[str]
    profit: Optional[str]
    expenses: Optional[str]
    ratios: list[str]


class PageSummaryItemV2(BaseModel):
    primary_category: str
    secondary_tags: list[str]
    summary: str
    key_entities: list[str]
    key_metrics: Optional[KeyMetricsV2]
    confidence: str


class DocumentSummaryResponseV2(BaseModel):
    items: list[PageSummaryItemV2]


class PageSummaryItemV3(BaseModel):
    primary_category: str
    secondary_tags: list[str]
    summary: str
    key_entities: list[str]
    key_metrics: Optional[KeyMetricsV2]
    confidence: str


class DocumentSummaryResponseV3(BaseModel):
    items: list[PageSummaryItemV3]


def get_response_model(version: str):
    if version == "v1":
        return SummaryResponseV1
    if version == "v2":
        return DocumentSummaryResponseV2
    if version == "v3":
        return DocumentSummaryResponseV3
    raise ValueError(f"Unknown model version: {version}")


def validate_response(model_cls, data):
    if hasattr(model_cls, "model_validate"):
        return model_cls.model_validate(data)
    return model_cls.parse_obj(data)


def _model_fields(model_cls) -> list[str]:
    if hasattr(model_cls, "model_fields"):
        return list(model_cls.model_fields.keys())
    return list(model_cls.__fields__.keys())


def _stringify_list(values):
    if values is None:
        return None
    return "; ".join(str(item) for item in values if item is not None)


def get_output_columns(version: str) -> list[str]:
    if version == "v1":
        return _model_fields(SectionSummaryV1)
    if version in {"v2", "v3"}:
        columns = []
        model_cls = PageSummaryItemV2 if version == "v2" else PageSummaryItemV3
        for field in _model_fields(model_cls):
            if field == "key_metrics":
                for subfield in _model_fields(KeyMetricsV2):
                    columns.append(f"key_metrics_{subfield}")
            else:
                columns.append(field)
        return columns
    raise ValueError(f"Unknown model version: {version}")


def model_to_rows(version: str, validated, fallback_text: str) -> list[dict[str, object]]:
    if version == "v1":
        if validated and getattr(validated, "sections", None):
            return [
                {"section": item.section, "summary": item.summary}
                for item in validated.sections
            ]
        return [{"section": "Full Document", "summary": fallback_text}]

    if version == "v2":
        if not validated or not getattr(validated, "items", None):
            return [
                {
                    "primary_category": None,
                    "secondary_tags": None,
                    "summary": fallback_text,
                    "key_entities": None,
                    "key_metrics_revenue": None,
                    "key_metrics_profit": None,
                    "key_metrics_expenses": None,
                    "key_metrics_ratios": None,
                    "confidence": None,
                }
            ]

        rows = []
        for item in validated.items:
            key_metrics = getattr(item, "key_metrics", None)
            rows.append(
                {
                    "primary_category": item.primary_category,
                    "secondary_tags": _stringify_list(item.secondary_tags),
                    "summary": item.summary,
                    "key_entities": _stringify_list(item.key_entities),
                    "key_metrics_revenue": getattr(key_metrics, "revenue", None),
                    "key_metrics_profit": getattr(key_metrics, "profit", None),
                    "key_metrics_expenses": getattr(key_metrics, "expenses", None),
                    "key_metrics_ratios": _stringify_list(
                        getattr(key_metrics, "ratios", None)
                    ),
                    "confidence": item.confidence,
                }
            )
        return rows

    if version == "v3":
        if not validated or not getattr(validated, "items", None):
            return [
                {
                    "primary_category": None,
                    "secondary_tags": None,
                    "summary": fallback_text,
                    "key_entities": None,
                    "key_metrics_revenue": None,
                    "key_metrics_profit": None,
                    "key_metrics_expenses": None,
                    "key_metrics_ratios": None,
                    "confidence": None,
                }
            ]

        rows = []
        for item in validated.items:
            key_metrics = getattr(item, "key_metrics", None)
            rows.append(
                {
                    "primary_category": item.primary_category,
                    "secondary_tags": _stringify_list(item.secondary_tags),
                    "summary": item.summary,
                    "key_entities": _stringify_list(item.key_entities),
                    "key_metrics_revenue": getattr(key_metrics, "revenue", None),
                    "key_metrics_profit": getattr(key_metrics, "profit", None),
                    "key_metrics_expenses": getattr(key_metrics, "expenses", None),
                    "key_metrics_ratios": _stringify_list(
                        getattr(key_metrics, "ratios", None)
                    ),
                    "confidence": item.confidence,
                }
            )
        return rows

    raise ValueError(f"Unknown model version: {version}")
