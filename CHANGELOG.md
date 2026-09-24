# Changelog

## 0.3.0 - Development

### Added

- Added the first bundled `Oceamo ICP Card` for Home Assistant dashboards.
- The integration now serves and automatically loads the card through the Home Assistant frontend.
- No separate HACS frontend repository or manual Lovelace resource entry is required.
- Added a visual editor for choosing the `ICP Status` entity, an optional title and previous-analysis display.
- Card shows analysis metadata, overall status, status counts, collapsible categories, targets, previous values, deltas and trend direction.
- Added German and English card labels.
- Added mobile-responsive card styling.

### Changed

- Added `frontend` as an integration dependency.
- Updated the README with card installation and usage instructions.

## 0.2.5 - Development

### Added

- Added comparison data between the latest ICP and the immediately previous stored ICP.
- Each current measurement now exposes `has_previous`, `previous_value`, `previous_raw_value`, `previous_display_value`, previous report metadata, `delta` and `trend`.
- The `ICP Status` sensor now exposes the same enriched measurement list for the future dashboard card.
- Added previous analysis metadata to the `ICP Status` sensor.

### Changed

- Updated the README to reflect long-term statistics, the analysis-number entity and historical comparison support.

## 0.2.4 - Development

### Fixed

- Added a one-time entity-registry migration for the `Analysis number` sensor.
- Keeps the existing entity ID and user customizations while moving the sensor
  to a fresh unique ID.
- Removes a stale unavailable state before the migrated entity is re-added.
- This targets installations where the analysis-number sensor was introduced
  after the Oceamo config entry already existed.

## 0.2.3 - Development

### Fixed

- Made all PDF-backed Oceamo sensors explicitly non-polling.
- Simplified the `Analysis number` sensor to publish its string value and attributes directly during entity creation.

## 0.2.2 - Development

### Added

- Added a dedicated `Analysis number` sensor for the newest imported Oceamo report.
- The analysis-number sensor also exposes analysis date, sample timestamp and tank type as attributes.

## 0.2.1 - Development

### Fixed

- Fixed invalid external statistic IDs on Home Assistant installations using uppercase config-entry IDs.
- Statistic IDs are now normalized to lowercase Home Assistant-compatible slugs before import.

## 0.2.0 - Development

### Added

- Historical ICP values as Home Assistant external long-term statistics.
- Statistics use the original sample timestamp from each Oceamo report.
- Sample timestamps are rounded down to the hour because Home Assistant external statistics require hourly timestamps.
- Numeric ICP values are stored with mean/min/max values for graphing.
- `n.n.` and `n.b.` values are never converted to numeric zero.
- `historical_statistic_id` attribute on measurement sensors.
- `display_value` attribute, including `Nicht nachweisbar` and `Nicht bestimmt`.
- Compact `stored_reports` history on the `ICP Status` sensor.

### Changed

- Added `recorder` as a dependency.

## 0.1.0 - Development

### Added

- Initial HACS-compatible Home Assistant integration structure.
- PDF upload through the Home Assistant config flow.
- Parser for classic Oceamo ICP PDF reports.
- Parsing of metadata, measurement groups, target values and non-detects.
- Extraction of Oceamo green/yellow/red status icons from the tested classic report format.
- Sensor entities for ICP parameters.
- A report/status sensor intended as the data source for the future custom dashboard card.
- Import of additional PDFs through the integration options flow.
