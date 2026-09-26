"""Test bootstrap for Reef ICP pure-Python modules.

The integration package's __init__.py imports Home Assistant runtime modules.
These tests deliberately exercise parser/recommendation code without requiring a
full Home Assistant installation, so a lightweight namespace package is used.
"""

from __future__ import annotations

from pathlib import Path
import sys
import types


ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "reef_icp"

custom_components = types.ModuleType("custom_components")
custom_components.__path__ = [str(ROOT / "custom_components")]
sys.modules.setdefault("custom_components", custom_components)

reef_icp = types.ModuleType("custom_components.reef_icp")
reef_icp.__path__ = [str(INTEGRATION)]
sys.modules.setdefault("custom_components.reef_icp", reef_icp)
