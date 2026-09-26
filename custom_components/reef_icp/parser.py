"""Provider-dispatch wrapper for Reef ICP.

The established Oceamo, Fauna Marin, ATI and TRITON parsers remain unchanged in
``parser_core.py``. This module adds Tropic Marin while preserving the public
parser API used by Home Assistant's config flow.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .parser_core import *  # noqa: F403
from .parser_core import (
    PROVIDER_NAMES as _CORE_PROVIDER_NAMES,
    detect_icp_provider as _detect_core_provider,
    parse_icp_pdf_for_provider as _parse_core_provider,
)
from .tropic_marin import (
    PROVIDER_TROPIC_MARIN,
    PROVIDER_TROPIC_MARIN_NAME,
    looks_like_tropic_marin_pdf,
    parse_tropic_marin_pdf,
)

PROVIDER_NAMES = {
    **_CORE_PROVIDER_NAMES,
    PROVIDER_TROPIC_MARIN: PROVIDER_TROPIC_MARIN_NAME,
}


def _normalize_osmosis_display_names(report: dict[str, Any]) -> dict[str, Any]:
    """Give every RO/osmosis result an unambiguous visible name.

    The category/key stay untouched so Home Assistant entity identities and
    long-term statistics remain stable across this presentation-only change.
    """
    for measurement in report.get("measurements", []):
        if not isinstance(measurement, dict):
            continue
        if measurement.get("category") != "osmosis":
            continue

        name = str(measurement.get("name") or "").strip()
        if name and not name.casefold().endswith("(osmose)"):
            measurement["name"] = f"{name} (Osmose)"

    return report


def detect_icp_provider(path: str | Path) -> str:
    """Detect Tropic Marin first, then use the established provider detector."""
    if looks_like_tropic_marin_pdf(path):
        return PROVIDER_TROPIC_MARIN
    return _detect_core_provider(path)


def parse_icp_pdf_for_provider(
    path: str | Path,
    provider: str,
    analysis_date_override: str | None = None,
) -> dict[str, Any]:
    """Parse a PDF with the explicitly selected provider parser."""
    if provider == PROVIDER_TROPIC_MARIN:
        report = parse_tropic_marin_pdf(path, analysis_date_override)
    else:
        report = _parse_core_provider(path, provider, analysis_date_override)
    return _normalize_osmosis_display_names(report)


def parse_icp_pdf(
    path: str | Path,
    analysis_date_override: str | None = None,
) -> dict[str, Any]:
    """Detect the provider and dispatch the uploaded PDF."""
    provider = detect_icp_provider(path)
    return parse_icp_pdf_for_provider(path, provider, analysis_date_override)
