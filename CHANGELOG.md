# Changelog

## 0.2.3 - Development

### Fixed

- Made all PDF-backed Oceamo sensors explicitly non-polling.
- Simplified the `Analysis number` sensor to publish its string value and attributes directly during entity creation.
- Intended to prevent the analysis-number entity from becoming unavailable after initial setup/reload.

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
- Integration version bumped to 0.2.0.

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
