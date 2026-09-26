# Reef ICP support matrix

This document separates **report parsing** from **supply-system correction support**.
A parsed element does not automatically mean Reef ICP will calculate a dose for it.
Numeric correction rules are added only when a manufacturer publishes an unambiguous
product strength and, where applicable, a maximum daily correction.

## ICP providers

| Provider | Aquarium water | RO / osmosis water | History / comparison |
| --- | --- | --- | --- |
| Oceamo | ✅ | ✅ when present in the report | ✅ |
| ATI | ✅ | provider/report dependent | ✅ |
| Fauna Marin | ✅ | provider/report dependent | ✅ |
| TRITON | ✅ | provider/report dependent | ✅ |
| Tropic Marin | ✅ | ✅ with Water Analysis Plus | ✅ |

## Supply systems

| System | Core correction | Individual element correction | Trace-element strategy |
| --- | --- | --- | --- |
| Fauna Marin Balling Light | ✅ Ca / Mg / KH | ✅ Elementals / Elementals Trace | Numeric manufacturer rules where published |
| ATI Essentials pro | ✅ via ATI ICP Elements | ✅ broad ATI ICP Elements coverage | Numeric manufacturer rules where published |
| Oceamo DUO | ✅ KH plus supported auxiliary corrections | ✅ supported Single Elements | Numeric manufacturer rules where published; ICP-MS restriction kept for selenium |
| TRITON Method / Core7 | ✅ maintenance guidance | ✅ supported analytes | Uses the official TRITON calculator instead of inventing a concentration formula |
| Tropic Marin Original Balling | ✅ Part A / Part B | ✅ Mg, K, I, Br, Fe in 0.14.0 | K+ Elements / A- Elements retained as published maintenance guidance; no invented per-element strength |

## Tropic Marin sources used for 0.14.0

- Original Balling: https://www.tropic-marin-smartinfo.com/original-balling-components
- Bio-Magnesium: https://www.tropic-marin-smartinfo.com/bio-magnesium
- Potassium: https://www.tropic-marin-smartinfo.com/potassium
- Iodine: https://www.tropic-marin-smartinfo.com/iodine
- Bromine: https://www.tropic-marin-smartinfo.com/bromine
- Iron: https://www.tropic-marin-smartinfo.com/iron
- K+ Elements: https://www.tropic-marin-smartinfo.com/k-elements
- A- Elements: https://www.tropic-marin-smartinfo.com/a-elements

## Safety boundary

RO / osmosis measurements are diagnostic source-water measurements. They are excluded
from aquarium dosing recommendations even when their normalized analyte key matches an
aquarium-water parameter such as calcium, potassium or iodine.
