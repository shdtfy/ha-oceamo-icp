"""Constants for the Reef ICP integration."""

# The legacy domain is intentionally retained so existing Oceamo ICP
# installations, entities, statistics and dashboard resources keep working.
DOMAIN = "oceamo_icp"

CONF_AQUARIUM_NAME = "aquarium_name"
CONF_AQUARIUM_VOLUME_L = "aquarium_volume_l"
CONF_SUPPLY_SYSTEM = "supply_system"
CONF_REPORTS = "reports"

SUPPLY_SYSTEM_NONE = "none"
SUPPLY_SYSTEM_FAUNA_MARIN_BALLING_LIGHT = "fauna_marin_balling_light"
SUPPLY_SYSTEM_ATI_ESSENTIALS_PRO = "ati_essentials_pro"
SUPPLY_SYSTEM_TRITON_METHOD = "triton_method"
SUPPLY_SYSTEM_OCEAMO_DUO = "oceamo_duo"

SUPPLY_SYSTEM_NAMES = {
    SUPPLY_SYSTEM_NONE: "None / analysis only",
    SUPPLY_SYSTEM_FAUNA_MARIN_BALLING_LIGHT: "Fauna Marin Balling Light",
    SUPPLY_SYSTEM_ATI_ESSENTIALS_PRO: "ATI Essentials pro",
    SUPPLY_SYSTEM_TRITON_METHOD: "TRITON Method",
    SUPPLY_SYSTEM_OCEAMO_DUO: "Oceamo DUO",
}

PROVIDER_OCEAMO = "oceamo"
PROVIDER_FAUNA_MARIN = "fauna_marin"
PROVIDER_ATI = "ati"

MAX_STORED_REPORTS = 100
