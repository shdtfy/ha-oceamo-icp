"""Runtime extensions for Reef ICP 0.15.0 sensor attributes.

The core sensor platform remains untouched. This module adds the independent
reef/nutrient-method profile fields and its manufacturer-guidance payload to the
existing ICP Status sensor.
"""

from __future__ import annotations

from typing import Any

from .const import (
    CONF_REEF_METHOD,
    REEF_METHOD_NAMES,
    REEF_METHOD_NONE,
)
from .reef_methods import build_reef_method_guidance

_PATCHED = False


def apply_sensor_extensions() -> None:
    """Patch the already-loaded sensor module exactly once."""
    global _PATCHED
    if _PATCHED:
        return

    from . import sensor as legacy

    original_profile = legacy._aquarium_profile
    original_extra_property = legacy.ReefReportSensor.extra_state_attributes
    original_extra = original_extra_property.fget
    if original_extra is None:
        raise RuntimeError("ReefReportSensor.extra_state_attributes has no getter")

    def aquarium_profile(entry: Any) -> dict[str, Any]:
        profile = dict(original_profile(entry))
        method = entry.options.get(CONF_REEF_METHOD, REEF_METHOD_NONE)
        profile.update(
            {
                "reef_method": method,
                "reef_method_name": REEF_METHOD_NAMES.get(str(method), str(method)),
            }
        )
        return profile

    def extra_state_attributes(self: Any) -> dict[str, Any]:
        attrs = dict(original_extra(self))
        method = attrs.get("reef_method") or REEF_METHOD_NONE
        attrs["reef_method_guidance"] = build_reef_method_guidance(
            str(method),
            attrs.get("aquarium_volume_l"),
            self._measurements,
            attrs.get("stocking_profile"),
        )
        return attrs

    legacy._aquarium_profile = aquarium_profile
    legacy.ReefReportSensor.extra_state_attributes = property(extra_state_attributes)
    _PATCHED = True
