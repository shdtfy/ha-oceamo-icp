# Reef ICP support matrix

Reef ICP separates **ICP report parsing**, **mineral / dosing supply systems** and
**reef / nutrient methods**. They are intentionally independent: a tank can,
for example, use Fauna Marin Balling Light while running Fauna Marin ZEO LIGHT.

Numeric correction rules are only added when a manufacturer publishes an
unambiguous product strength. Mixed maintenance systems and proprietary
calculators remain manufacturer-guided rather than receiving invented formulas.

## ICP providers

| Provider | Aquarium water | RO / osmosis water | History / comparison |
| --- | --- | --- | --- |
| Oceamo | ✅ | ✅ when present in the report | ✅ |
| ATI | ✅ | provider/report dependent | ✅ |
| Fauna Marin | ✅ | provider/report dependent | ✅ |
| TRITON | ✅ | provider/report dependent | ✅ |
| Tropic Marin | ✅ | ✅ with Water Analysis Plus | ✅ |

## Mineral / dosing supply systems

| System | Core correction | Individual element correction | Strategy |
| --- | --- | --- | --- |
| Fauna Marin Balling Light | ✅ Ca / Mg / KH | ✅ Elementals / Elementals Trace | Numeric manufacturer rules where published |
| ATI Essentials pro | ✅ via ATI ICP Elements | ✅ broad ATI ICP Elements coverage | Numeric manufacturer rules where published |
| Oceamo DUO | ✅ KH plus supported auxiliary corrections | ✅ supported Single Elements | Numeric manufacturer rules where published |
| TRITON Method / Core7 | ✅ maintenance guidance | ✅ supported analytes | Official TRITON calculator |
| Tropic Marin Original Balling | ✅ Part A / Part B | ✅ Mg, K, I, Br, Fe | Published numeric correction rules |
| Tropic Marin All-For-Reef | ✅ maintenance | included in balanced product | Published start / increment / maximum maintenance dose |
| Aquaforest Component 1+2+3+ | ✅ equal-part maintenance | included in balanced products | Equal dosing preserved; individual imbalance uses separate supplements |
| Red Sea Reef Care 4-Part | ✅ manufacturer guidance | manufacturer guidance | No cross-generation concentration assumptions |
| Red Sea Reef Care 7-Part | ✅ manufacturer guidance | manufacturer guidance | No cross-generation concentration assumptions |
| SANGOKAI BALANCE + INDIVIDUAL | ✅ Ca / KH | ✅ K, Sr, B, Br, I | Published numeric working-solution / INDIVIDUAL strengths |
| Korallen-Zucht Coral System 1-4 | separate Ca/KH/Mg required | trace/mineral maintenance | Published weekly maintenance dose |
| Reef Zlements | system maintenance | ✅ via official ICP portal | Official portal, no reverse-engineered concentrations |
| Reef Moonshiner's | method/tool driven | ✅ via official Assessment & Dosing Tools | Official tools, no reverse-engineered formulas |

## Reef / nutrient methods

| Method | Volume-scaled guidance | Included guidance |
| --- | --- | --- |
| Korallen-Zucht ZEOvit | ✅ | media volume, long-term reactor flow, 6-8 week change, daily cleaning |
| Fauna Marin ZEO LIGHT | ✅ | zeolite, Reef Vitality, Carb L, Color Elements, Coral Sprint, Min S |
| Aquaforest Zeo Mix | ✅ | media amount, reactor flow, 6-week replacement |
| Aquaforest Probiotic Method | ✅ | Pro Bio S + -NP Pro daily dose |
| Brightwell NeoZeo | ✅ | staged weeks 1-5 setup plus 6-week maintenance cycle |
| SANGOKAI BASIS | ✅ | establishment ramp and PO4-dependent long-term dose |
| Red Sea NO3:PO4-X | ✅ | stocking-profile-based average daily manufacturer dose |

## Safety boundaries

- RO / osmosis measurements are excluded from aquarium supplement and reef-method dosing calculations.
- Balanced multi-component systems are not deliberately unbalanced when the manufacturer instructs equal dosing.
- Proprietary manufacturer calculators are linked instead of reverse-engineered.
- ZEOvit long-term guidance is not silently reused for tank conversion/startup, which uses different flow regimes.
