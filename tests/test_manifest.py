"""Repository-level release metadata tests."""

from __future__ import annotations

import json
from pathlib import Path


def test_manifest_version_is_current_release_candidate() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads(
        (root / "custom_components" / "reef_icp" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["domain"] == "reef_icp"
    assert manifest["version"] == "0.14.0"
    assert "pypdf==6.19.0" in manifest["requirements"]
