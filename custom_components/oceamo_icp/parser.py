"""Parser for Oceamo ICP PDF reports."""

from __future__ import annotations

from datetime import datetime
import hashlib
from pathlib import Path
import re
from typing import Any
import unicodedata

from pypdf import PdfReader
from pypdf.generic import ContentStream


class OceamoParseError(ValueError):
    """Raised when an Oceamo report cannot be parsed."""


CATEGORY_HEADINGS = {
    "Grundparameter": "basic",
    "Mengenelemente": "major_elements",
    "Spurenelemente": "trace_elements",
    "Schadstoffe": "pollutants",
    "Nährstoffe": "nutrients",
    "Osmose-Check": "osmosis",
}

# MD5 hashes of the decoded 15x15 status artwork embedded in the tested
# classic Oceamo PDF format. Unknown artwork is deliberately not guessed.
_STATUS_IMAGE_HASHES: dict[str, dict[str, str | None]] = {
    "3346ccd496a836a16d810b48ef46ffb9": {
        "severity": "ok",
        "direction": None,
    },
    "82766212f5f1f90277061b6ade0004c7": {
        "severity": "critical",
        "direction": "high",
    },
    "4dd707d862ed26bdee6a3119fcbaf1f1": {
        "severity": "critical",
        "direction": "low",
    },
    "c890e5b25e13d2fbe08b73348bf632fe": {
        "severity": "warning",
        "direction": "high",
    },
    "7816fa4e75cd34b2df783e0253d4edb6": {
        "severity": "warning",
        "direction": "low",
    },
}

_UNIT_PATTERN = r"(?:psu|dKH|mg/l|µg/l|μg/l|ng/l|mmol/l|µmol/l|μmol/l)"

_ROW_RE = re.compile(
    rf"^(?P<name>.+?)\s+"
    rf"(?P<value>n\.n\.|n\.b\.|-?\d+(?:[.,]\d+)?)\s+"
    rf"(?:(?P<unit>{_UNIT_PATTERN})\s+)?"
    rf"(?P<target>"
    rf"n\.n\.|n\.b\.|"
    rf"<\s*-?\d+(?:[.,]\d+)?|"
    rf">\s*-?\d+(?:[.,]\d+)?|"
    rf"-?\d+(?:[.,]\d+)?(?:\s*-\s*-?\d+(?:[.,]\d+)?)?"
    rf")"
    rf"(?:\s+(?P<target_unit>{_UNIT_PATTERN}))?\s*$"
)


def _decimal(value: str) -> float:
    """Convert a German/English decimal string to float."""
    return float(value.replace(",", "."))


def _slug(value: str) -> str:
    """Create a stable ASCII key."""
    value = (
        value.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("Ä", "Ae")
        .replace("Ö", "Oe")
        .replace("Ü", "Ue")
        .replace("ß", "ss")
    )
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()


def _parse_date(value: str) -> str:
    """Convert DD.MM.YYYY to ISO date."""
    return datetime.strptime(value, "%d.%m.%Y").date().isoformat()


def _parse_sample_datetime(value: str) -> str:
    """Convert Oceamo sample timestamp to an ISO local datetime string."""
    normalized = re.sub(r"\s+", " ", value.strip())
    return datetime.strptime(normalized, "%d.%m.%Y - %H:%M").isoformat()


def _parse_target(raw: str) -> dict[str, Any]:
    """Parse the ideal/target value representation."""
    normalized = raw.replace(" ", "")

    if normalized == "n.n.":
        return {"type": "not_detectable"}
    if normalized == "n.b.":
        return {"type": "not_determined"}
    if normalized.startswith("<"):
        return {"type": "upper_limit", "max": _decimal(normalized[1:])}
    if normalized.startswith(">"):
        return {"type": "lower_limit", "min": _decimal(normalized[1:])}

    range_match = re.fullmatch(
        r"(-?\d+(?:[.,]\d+)?)\s*-\s*(-?\d+(?:[.,]\d+)?)", raw
    )
    if range_match:
        return {
            "type": "range",
            "min": _decimal(range_match.group(1)),
            "max": _decimal(range_match.group(2)),
        }

    return {"type": "exact", "value": _decimal(normalized)}


def _parse_measurement_line(
    line: str, category: str
) -> dict[str, Any] | None:
    """Parse one table row."""
    normalized = " ".join(line.split())
    match = _ROW_RE.match(normalized)
    if not match:
        return None

    raw_value = match.group("value")
    unit = match.group("unit") or match.group("target_unit")
    if unit is not None:
        unit = unit.replace("μ", "µ")

    measurement: dict[str, Any] = {
        "key": _slug(match.group("name")),
        "name": match.group("name"),
        "category": category,
        "raw_value": raw_value,
        "unit": unit,
        "target": _parse_target(match.group("target")),
    }

    if raw_value == "n.n.":
        measurement.update(
            {
                "value": None,
                "detected": False,
                "determined": True,
            }
        )
    elif raw_value == "n.b.":
        measurement.update(
            {
                "value": None,
                "detected": None,
                "determined": False,
            }
        )
    else:
        measurement.update(
            {
                "value": _decimal(raw_value),
                "detected": True,
                "determined": True,
            }
        )

    return measurement


def _extract_status_sequence(page: Any, reader: PdfReader) -> list[dict[str, Any]]:
    """Extract known Oceamo status icons in drawing order."""
    resources = page.get("/Resources")
    if resources is None:
        return []

    xobjects_ref = resources.get("/XObject")
    if xobjects_ref is None:
        return []

    xobjects = xobjects_ref.get_object()
    statuses_by_name: dict[str, dict[str, Any]] = {}

    for name, reference in xobjects.items():
        obj = reference.get_object()
        if (
            obj.get("/Subtype") != "/Image"
            or obj.get("/Width") != 15
            or obj.get("/Height") != 15
        ):
            continue

        try:
            digest = hashlib.md5(obj.get_data()).hexdigest()  # noqa: S324
        except Exception:  # noqa: BLE001
            continue

        if status := _STATUS_IMAGE_HASHES.get(digest):
            statuses_by_name[str(name)] = status

    if not statuses_by_name:
        return []

    try:
        content = ContentStream(page.get_contents(), reader)
    except Exception:  # noqa: BLE001
        return []

    result: list[dict[str, Any]] = []
    for operands, operator in content.operations:
        if operator != b"Do" or not operands:
            continue
        status = statuses_by_name.get(str(operands[0]))
        if status is not None:
            result.append(dict(status))

    return result


def _extract_metadata(text: str) -> dict[str, Any]:
    """Extract report metadata while deliberately omitting customer details."""
    metadata: dict[str, Any] = {}

    if match := re.search(r"Analysedatum:\s*(\d{2}\.\d{2}\.\d{4})", text):
        metadata["analysis_date"] = _parse_date(match.group(1))
    if match := re.search(r"Analysenummer:\s*([A-Za-z]{2}\d+)", text):
        metadata["analysis_number"] = match.group(1)
    if match := re.search(
        r"Probennahme:\s*(\d{2}\.\d{2}\.\d{4}\s*-\s*\d{2}:\d{2})",
        text,
    ):
        metadata["sample_taken"] = _parse_sample_datetime(match.group(1))
    if match := re.search(r"Beckentyp:\s*(.+?)(?:\n|$)", text):
        metadata["tank_type"] = match.group(1).strip()

    return metadata


def _extract_interpretation(text: str) -> str | None:
    """Extract Oceamo's interpretation section."""
    match = re.search(
        r"Interpretation\s+(.*?)\s+Produktempfehlungen",
        text,
        flags=re.DOTALL,
    )
    if not match:
        return None
    return " ".join(match.group(1).split())


def _extract_product_recommendations(text: str) -> str | None:
    """Extract the product recommendation block as source text."""
    match = re.search(
        r"Produktempfehlungen\s+(.*?)(?:Advanced Reef Chemistry|$)",
        text,
        flags=re.DOTALL,
    )
    if not match:
        return None
    value = " ".join(match.group(1).split())
    return value or None


def parse_oceamo_pdf(path: str | Path) -> dict[str, Any]:
    """Parse an Oceamo PDF report into JSON-serializable data."""
    try:
        reader = PdfReader(str(path))
    except Exception as err:  # noqa: BLE001
        raise OceamoParseError("The uploaded file is not a readable PDF.") from err

    page_texts = [(page.extract_text() or "") for page in reader.pages]
    full_text = "\n".join(page_texts)

    if "Oceamo" not in full_text or "Analysebericht" not in full_text:
        raise OceamoParseError("The PDF does not look like an Oceamo analysis report.")

    metadata = _extract_metadata(full_text)
    measurements: list[dict[str, Any]] = []
    current_category: str | None = None

    for page, page_text in zip(reader.pages, page_texts, strict=True):
        page_measurements: list[dict[str, Any]] = []

        for raw_line in page_text.splitlines():
            line = " ".join(raw_line.split())
            if not line:
                continue

            if line == "Interpretation":
                break

            if line in CATEGORY_HEADINGS:
                current_category = CATEGORY_HEADINGS[line]
                continue

            if current_category is None:
                continue

            if measurement := _parse_measurement_line(line, current_category):
                page_measurements.append(measurement)

        # The classic report draws one status icon per table row. Legend icons
        # are drawn after the data rows, so only consume as many as we parsed.
        page_statuses = _extract_status_sequence(page, reader)
        for index, measurement in enumerate(page_measurements):
            if index < len(page_statuses):
                measurement["status"] = page_statuses[index]
            else:
                measurement["status"] = {
                    "severity": "unknown",
                    "direction": None,
                }

        measurements.extend(page_measurements)

    if not measurements:
        raise OceamoParseError("No ICP measurements were found in the report.")

    if "analysis_number" not in metadata:
        raise OceamoParseError("The analysis number could not be found.")
    if "analysis_date" not in metadata:
        raise OceamoParseError("The analysis date could not be found.")

    return {
        "schema_version": 1,
        "metadata": metadata,
        "measurements": measurements,
        "interpretation": _extract_interpretation(full_text),
        "product_recommendations": _extract_product_recommendations(full_text),
    }
