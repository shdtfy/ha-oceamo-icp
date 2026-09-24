# Oceamo ICP for Home Assistant

A custom Home Assistant integration for importing Oceamo ICP analysis reports directly from PDF files.

> **Status:** Early development / alpha.

## What the first development version does

- Install as a HACS custom repository
- Add **Oceamo ICP** under **Settings → Devices & services**
- Upload an Oceamo PDF directly in the Home Assistant UI
- Parse report metadata, measurements, target values and Oceamo status icons
- Keep `n.n.` ("not detectable") separate from a numeric zero
- Create one Home Assistant sensor per ICP parameter
- Store multiple imported reports
- Import another PDF from the integration's **Configure** / options flow
- Expose one report/status entity containing the latest report for the future custom dashboard card

The parser currently targets the classic Oceamo report format used by analysis **OC188727** from 2022. Support for newer Oceamo and ICP-MS report formats will be added separately.

## Installation during development

1. Open HACS.
2. Add this repository as a custom repository:
   `https://github.com/shdtfy/ha-oceamo-icp`
3. Select category **Integration**.
4. Install **Oceamo ICP**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services → Add integration**.
7. Search for **Oceamo ICP**.
8. Enter an aquarium name and upload an Oceamo PDF.

## Current entities

The integration creates:

- `ICP Status` – summary state plus the latest report as attributes
- `Analysis date`
- One sensor for each parameter in the latest report

Parameters from the RO/DI water check use their own unique IDs, so names such as copper or zinc can exist both for aquarium water and RO/DI water.

## Roadmap

- [x] Classic Oceamo PDF parser
- [x] Oceamo status icon extraction for the tested classic report
- [x] Config flow with PDF upload
- [x] Sensor entities
- [x] Multiple stored reports
- [ ] Long-term statistics using the original analysis timestamp
- [ ] Dedicated Oceamo ICP dashboard card
- [ ] Newer Oceamo / ICP-MS report formats
- [ ] Automated tests and release workflow
- [ ] First tagged HACS release

## Privacy

Oceamo reports can contain names, customer numbers and other personal information. Reports are processed locally by Home Assistant. Test reports containing personal information are **not** included in this repository.

## Disclaimer

This project is an independent community integration and is not affiliated with or endorsed by Oceamo.
