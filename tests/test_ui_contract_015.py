"""Repository contract checks for the Reef ICP 0.15 profile/UI wiring."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "reef_icp"


def test_config_flow_exposes_independent_reef_method() -> None:
    source = (INTEGRATION / "config_flow.py").read_text(encoding="utf-8")
    assert "CONF_REEF_METHOD" in source
    assert "_reef_method_selector" in source
    assert "CONF_REEF_METHOD: reef_method" in source


def test_translations_label_reef_method() -> None:
    for path in (
        INTEGRATION / "strings.json",
        INTEGRATION / "translations" / "en.json",
        INTEGRATION / "translations" / "de.json",
    ):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "reef_method" in data["config"]["step"]["user"]["data"]
        assert "reef_method" in data["options"]["step"]["aquarium_settings"]["data"]


def test_card_extension_is_registered() -> None:
    init_source = (INTEGRATION / "__init__.py").read_text(encoding="utf-8")
    card_path = INTEGRATION / "www" / "reef-icp-card-v015.js"
    assert card_path.exists()
    assert "CARD_EXTENSION_URL" in init_source
    assert "reef-icp-card-v015.js" in init_source
    assert 'CARD_VERSION = "0.15.0"' in init_source


def test_sensor_extension_exposes_guidance_payload() -> None:
    source = (INTEGRATION / "sensor_v015.py").read_text(encoding="utf-8")
    assert '"reef_method"' in source
    assert '"reef_method_name"' in source
    assert 'attrs["reef_method_guidance"]' in source
    assert "build_reef_method_guidance" in source
