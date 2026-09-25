const CARD_VERSION = "0.12.0";
const CARD_TAG = "reef-icp-card";
const HISTORY_CARD_TAG = "reef-icp-history-card";

const CATEGORY_ORDER = [
  "basic",
  "major_elements",
  "trace_elements",
  "pollutants",
  "nutrients",
  "osmosis",
];

const CATEGORY_ICONS = {
  basic: "mdi:test-tube",
  major_elements: "mdi:atom",
  trace_elements: "mdi:molecule",
  pollutants: "mdi:alert-decagram-outline",
  nutrients: "mdi:sprout-outline",
  osmosis: "mdi:water-check-outline",
};

const TEXT = {
  de: {
    cardName: "Reef ICP",
    noEntity: "Bitte einen ICP-Status-Sensor auswählen.",
    entityMissing: "Die konfigurierte Entität ist nicht verfügbar.",
    invalidEntity: "Diese Entität enthält keine unterstützten ICP-Messwerte.",
    previous: "Vorher",
    target: "Soll",
    notDetectable: "Nicht nachweisbar",
    notDetermined: "Nicht bestimmt",
    unknown: "Unbekannt",
    ok: "Kein Handlungsbedarf",
    warning: "Beobachten",
    critical: "Handlungsbedarf",
    statusUnknown: "Status unbekannt",
    okShort: "OK",
    warningShort: "Warnung",
    criticalShort: "Kritisch",
    unknownShort: "Unklar",
    showPrevious: "Vorherige ICP anzeigen",
    entity: "ICP-Status-Entität",
    title: "Titel (optional)",
    improved: "Näher am Sollwert",
    worsened: "Weiter vom Sollwert entfernt",
    unchanged: "Abstand zum Sollwert unverändert",
    measurement: "Messwert",
    measurements: "Messwerte",
    history: "Verlauf",
    current: "Aktuell",
    change: "Veränderung",
    analyses: "Analysen",
    loadingHistory: "Verlauf wird geladen …",
    noHistory: "Für diesen Messwert sind noch keine numerischen Verlaufsdaten vorhanden.",
    historyError: "Die Verlaufsdaten konnten nicht geladen werden.",
    close: "Schließen",
    selectPoint: "Messpunkt auswählen",
    profileInsights: "Hinweise für dein Besatzprofil",
    profileContextFor: "Kontext für {profile}",
    profileHigh: "Besonders relevant",
    profileMedium: "Relevant",
    profileCurrentIssue: "Aktuell außerhalb des Labor-Sollbereichs",
    profileTrendUp: "Steigt seit {count} Messungen",
    profileTrendDown: "Fällt seit {count} Messungen",
    profileContextCarbonate: "Karbonatchemie",
    profileContextNutrients: "Nährstoffentwicklung",
    profileContextSalinity: "Salinität",
    profileReasonCarbonate: "KH und Calcium stehen direkt mit der Kalkskelettbildung von Steinkorallen in Verbindung. Reef ICP ändert deshalb aber keinen Labor-Sollbereich.",
    profileReasonNutrientsSps: "Nährstoffverläufe werden im SPS-Profil stärker hervorgehoben. Die Wirkung von Stickstoff und Phosphor ist arten-, konzentrations- und verhältnisabhängig, deshalb setzt Reef ICP keinen eigenen SPS-Sollwert.",
    profileReasonNutrients: "Nährstoffabweichungen werden für dieses Besatzprofil hervorgehoben. Der Sollbereich des Laborberichts bleibt unverändert.",
    profileReasonNutrientsFish: "Nährstoffabweichungen bleiben auch in einem Fish-Only-System für die Wasserqualität relevant. Reef ICP verwendet dafür weiterhin den Labor-Sollbereich.",
    profileReasonSalinity: "Salinitätsabweichungen und wiederholte Trends werden unabhängig vom Korallentyp hervorgehoben. Der Labor-Sollbereich bleibt maßgeblich.",
    profileBasisNote: "SPS und LPS sind praktische Aquaristik-Profile, keine strengen wissenschaftlichen Taxa. Diese Hinweise priorisieren nur die Aufmerksamkeit und verändern weder Laborstatus noch Sollwerte oder Dosierempfehlungen.",
    profileMore: "{count} weitere profilbezogene Hinweise werden nicht angezeigt.",
    changesSinceLast: "Seit der letzten ICP",
    comparedWith: "Verglichen mit",
    noStatusChanges: "Keine vergleichbaren Änderungen zum Sollbereich gegenüber der vorherigen ICP.",
    newIssue: "Neu außerhalb des Sollbereichs",
    resolved: "Wieder im Sollbereich",
    statusWorsened: "Weiter vom Soll entfernt",
    statusImproved: "Näher am Sollbereich",
    repeatedTrends: "Mehrfachtrends",
    trendUp: "Steigt seit {count} Messungen",
    trendDown: "Fällt seit {count} Messungen",
    trendFromTo: "Von {from} auf {to}",
    trendMore: "{count} weitere Trends werden nicht angezeigt.",
    trendNote: "Mehrfachtrends beschreiben nur die Richtung der gemessenen Werte. Sie bedeuten nicht automatisch, dass sich das Aquarium biologisch verbessert oder verschlechtert.",
    interpretation: "Interpretation des Labors",
    laboratoryRecommendations: "Empfehlungen aus dem Laborbericht",
    laboratoryFromReport: "Direkt aus {provider}",
    laboratoryDose: "Dosierung laut Laborbericht",
    laboratoryWaterChange: "Wasserwechsel laut Laborbericht empfohlen.",
    laboratoryCorrection: "Korrektur / einmalig",
    laboratoryMaintenance: "Erhaltung / täglich",
    laboratoryReportVolume: "Berichtsvolumen",
    laboratoryAdditionalText: "Weitere Produktempfehlung des Labors",
    laboratorySourceNote: "Diese Angaben stammen direkt aus dem importierten Laborbericht. Reef ICP berechnet oder verändert sie nicht und sie sind unabhängig vom ausgewählten Versorgungssystem.",
    laboratoryDoseBadge: "Labor-Dosierung",
    laboratoryHintBadge: "Labor-Hinweis",
    day: "Tag",
    days: "Tage",
    netVolume: "Netto",
    noSupplySystem: "Nur Analyse",
    supplyRecommendations: "Empfehlungen für dein Versorgungssystem",
    correctionDose: "Gesamte Korrekturdosis",
    reduceOrPause: "Nicht zusätzlich dosieren. Zugabe dieses Produkts bzw. der entsprechenden Systemkomponente vorerst reduzieren oder pausieren.",
    noCorrection: "Für die derzeit unterstützten Parameter ist anhand dieser Analyse keine Korrektur nötig.",
    singleElement: "Einzelelement",
    coreCorrection: "Grundversorgung",
    correctionOnly: "Korrekturdosen gleichen einen aktuellen Messwert aus. Die laufende Tagesdosierung des Versorgungssystems richtet sich weiterhin nach dem tatsächlichen Verbrauch.",
    splitDose: "Mindestens {days} Tage · ca. {dose} {unit}/Tag",
    dailyIncrease: "Rechnerischer Anstieg: ca. +{amount} {unit}/Tag",
    smallDose: "Kleine Dosiermenge: mit einer fein graduierten Spritze oder Pipette genau abmessen.",
    dailyLimitUnknown: "Für dieses Produkt ist in Reef ICP noch kein offizielles Tageslimit hinterlegt. Die Gesamtkorrektur daher nicht automatisch als Einmaldosis verstehen.",
    officialCalculator: "TRITON veröffentlicht die Dosierformel über den eigenen Herstellerrechner. Reef ICP erfindet dafür keine Konzentration.",
    requiresIcpMs: "Selenkorrektur nur auf Basis einer ICP-MS-Analyse. Oceamo weist darauf hin, dass der Optimalbereich unter der sicheren Nachweisgrenze von ICP-OES liegt.",
    openManufacturer: "Herstellerquelle öffnen",
    recommendationUnavailable: "Für dieses Versorgungssystem ist die automatische Dosierberechnung noch nicht hinterlegt.",
    maintenance_balling_light_consumption: "Die dauerhafte Balling-Light-Tagesdosis weiterhin am realen KH-/Calciumverbrauch ausrichten.",
    maintenance_ati_essentials_consumption: "ATI Essentials pro ist verbrauchsgeführt. Die laufende Dosierung anhand des 24-h-KH-Verbrauchs und des Calciumverlaufs einstellen.",
    maintenance_oceamo_duo_consumption: "Oceamo DUO ist verbrauchsgeführt. Die laufende DUO-Dosierung anhand von KH- und Calciumtrend einstellen.",
    maintenance_triton_core7_consumption: "TRITON Core7 Flex ist verbrauchsgeführt. Die laufende Dosis anhand des 24-h-KH-Verbrauchs mit dem offiziellen Core7-Rechner einstellen.",
    categories: {
      basic: "Grundparameter",
      major_elements: "Mengenelemente",
      trace_elements: "Spurenelemente",
      pollutants: "Schadstoffe",
      nutrients: "Nährstoffe",
      osmosis: "Osmose-Check",
      unknown: "Weitere Werte",
    },
  },
  en: {
    cardName: "Reef ICP",
    noEntity: "Please select an ICP status sensor.",
    entityMissing: "The configured entity is not available.",
    invalidEntity: "This entity does not contain supported ICP measurements.",
    previous: "Previous",
    target: "Target",
    notDetectable: "Not detectable",
    notDetermined: "Not determined",
    unknown: "Unknown",
    ok: "No action required",
    warning: "Observe",
    critical: "Action required",
    statusUnknown: "Status unknown",
    okShort: "OK",
    warningShort: "Warning",
    criticalShort: "Critical",
    unknownShort: "Unknown",
    showPrevious: "Show previous ICP",
    entity: "ICP status entity",
    title: "Title (optional)",
    improved: "Closer to target",
    worsened: "Further from target",
    unchanged: "Target distance unchanged",
    measurement: "measurement",
    measurements: "measurements",
    history: "History",
    current: "Current",
    change: "Change",
    analyses: "analyses",
    loadingHistory: "Loading history …",
    noHistory: "No numeric history is available for this measurement yet.",
    historyError: "The history data could not be loaded.",
    close: "Close",
    selectPoint: "Select data point",
    profileInsights: "Stocking profile insights",
    profileContextFor: "Context for {profile}",
    profileHigh: "Especially relevant",
    profileMedium: "Relevant",
    profileCurrentIssue: "Currently outside the laboratory target range",
    profileTrendUp: "Rising for {count} measurements",
    profileTrendDown: "Falling for {count} measurements",
    profileContextCarbonate: "Carbonate chemistry",
    profileContextNutrients: "Nutrient trend",
    profileContextSalinity: "Salinity",
    profileReasonCarbonate: "Alkalinity and calcium are directly involved in stony-coral skeletal calcification. Reef ICP therefore highlights them without changing the laboratory target range.",
    profileReasonNutrientsSps: "Nutrient trends receive extra attention in the SPS profile. Nitrogen and phosphorus effects depend on species, concentration and nutrient balance, so Reef ICP does not apply a separate SPS target range.",
    profileReasonNutrients: "Nutrient deviations are highlighted for this stocking profile. The laboratory target range remains unchanged.",
    profileReasonNutrientsFish: "Nutrient deviations remain relevant to water quality in a fish-only system. Reef ICP continues to use the laboratory target range.",
    profileReasonSalinity: "Salinity deviations and repeated trends are highlighted regardless of coral type. The laboratory target range remains authoritative.",
    profileBasisNote: "SPS and LPS are practical aquarium husbandry profiles, not strict scientific taxa. These hints only prioritize attention and do not alter laboratory status, target ranges or dosing recommendations.",
    profileMore: "{count} additional profile-related insights are not shown.",
    changesSinceLast: "Since the previous ICP",
    comparedWith: "Compared with",
    noStatusChanges: "No comparable target-range changes versus the previous ICP.",
    newIssue: "Newly outside target",
    resolved: "Back inside target",
    statusWorsened: "Further from target",
    statusImproved: "Closer to target",
    repeatedTrends: "Repeated trends",
    trendUp: "Rising for {count} measurements",
    trendDown: "Falling for {count} measurements",
    trendFromTo: "From {from} to {to}",
    trendMore: "{count} additional trends are not shown.",
    trendNote: "Repeated trends describe only the direction of measured values. They do not automatically mean that the aquarium has biologically improved or worsened.",
    interpretation: "Laboratory interpretation",
    laboratoryRecommendations: "Recommendations from the laboratory report",
    laboratoryFromReport: "Directly from {provider}",
    laboratoryDose: "Dose stated in laboratory report",
    laboratoryWaterChange: "Water change recommended by the laboratory report.",
    laboratoryCorrection: "Correction / one-time",
    laboratoryMaintenance: "Maintenance / daily",
    laboratoryReportVolume: "Report volume",
    laboratoryAdditionalText: "Additional laboratory product recommendation",
    laboratorySourceNote: "These values come directly from the imported laboratory report. Reef ICP does not recalculate or alter them and they are independent of the selected supply system.",
    laboratoryDoseBadge: "Lab dose",
    laboratoryHintBadge: "Lab note",
    day: "day",
    days: "days",
    netVolume: "Net",
    noSupplySystem: "Analysis only",
    supplyRecommendations: "Recommendations for your supply system",
    correctionDose: "Total correction dose",
    reduceOrPause: "Do not add more. Reduce or pause this product or the corresponding system component for now.",
    noCorrection: "No correction is required for the currently supported parameters based on this analysis.",
    singleElement: "Single element",
    coreCorrection: "Core supply",
    correctionOnly: "Correction doses bring a current measurement back toward target. Ongoing daily dosing of the supply system must still follow actual consumption.",
    splitDose: "At least {days} days · approx. {dose} {unit}/day",
    dailyIncrease: "Calculated increase: approx. +{amount} {unit}/day",
    smallDose: "Small dose: measure precisely with a finely graduated syringe or pipette.",
    dailyLimitUnknown: "Reef ICP does not yet have an official daily limit for this product. Do not automatically treat the total correction as a one-time dose.",
    officialCalculator: "TRITON publishes the dosing formula through its official calculator. Reef ICP does not invent a concentration for it.",
    requiresIcpMs: "Selenium correction requires an ICP-MS analysis. Oceamo states that the target range is below the reliable detection limit of ICP-OES.",
    openManufacturer: "Open manufacturer source",
    recommendationUnavailable: "Automatic dosing calculations are not yet available for this supply system.",
    maintenance_balling_light_consumption: "Keep the permanent Balling Light daily dose aligned with actual alkalinity/calcium consumption.",
    maintenance_ati_essentials_consumption: "ATI Essentials pro is consumption-driven. Set ongoing dosing from 24-hour alkalinity consumption and the calcium trend.",
    maintenance_oceamo_duo_consumption: "Oceamo DUO is consumption-driven. Set ongoing DUO dosing from alkalinity and calcium trends.",
    maintenance_triton_core7_consumption: "TRITON Core7 Flex is consumption-driven. Set ongoing dosing from 24-hour alkalinity consumption using the official Core7 calculator.",
    categories: {
      basic: "Basic parameters",
      major_elements: "Major elements",
      trace_elements: "Trace elements",
      pollutants: "Pollutants",
      nutrients: "Nutrients",
      osmosis: "RO/DI check",
      unknown: "Other values",
    },
  },
};

function languageFor(hass) {
  const language = hass?.language || hass?.locale?.language || "en";
  return language.toLowerCase().startsWith("de") ? "de" : "en";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function dateLabel(value, language) {
  if (!value) return "";
  const parsed = new Date(`${value}T12:00:00`);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return new Intl.DateTimeFormat(language === "de" ? "de-DE" : "en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(parsed);
}

function numericLabel(value, language, digits = 6) {
  if (typeof value !== "number" || Number.isNaN(value)) return "";
  return new Intl.NumberFormat(language === "de" ? "de-DE" : "en-GB", {
    maximumFractionDigits: digits,
  }).format(value);
}

function measurementValue(measurement, language, previous = false) {
  const raw = previous
    ? measurement.previous_raw_value
    : measurement.raw_value;
  const numeric = previous
    ? measurement.previous_value
    : measurement.value;

  if (raw === "n.n.") return TEXT[language].notDetectable;
  if (raw === "n.b." || raw === "n.g.") return TEXT[language].notDetermined;

  let display;
  if (raw !== undefined && raw !== null && raw !== "") {
    display = String(raw);
  } else if (typeof numeric === "number") {
    display = numericLabel(numeric, language);
  } else {
    return TEXT[language].unknown;
  }

  return measurement.unit ? `${display} ${measurement.unit}` : display;
}

function targetLabel(measurement, language) {
  const target = measurement.target;
  if (!target || !target.type) return "";

  const unit = measurement.unit ? ` ${measurement.unit}` : "";
  const n = (value) => numericLabel(value, language);

  switch (target.type) {
    case "exact":
      return `${n(target.value)}${unit}`;
    case "range":
      return `${n(target.min)}–${n(target.max)}${unit}`;
    case "upper_limit":
      return `< ${n(target.max)}${unit}`;
    case "lower_limit":
      return `> ${n(target.min)}${unit}`;
    case "not_detectable":
      return TEXT[language].notDetectable;
    case "not_determined":
      return TEXT[language].notDetermined;
    default:
      return "";
  }
}

function trendSymbol(trend) {
  if (trend === "up") return "↑";
  if (trend === "down") return "↓";
  if (trend === "same") return "→";
  return "";
}

function targetDistance(value, target) {
  if (typeof value !== "number" || Number.isNaN(value) || !target?.type) {
    return null;
  }

  switch (target.type) {
    case "exact":
      return typeof target.value === "number"
        ? Math.abs(value - target.value)
        : null;
    case "range":
      if (typeof target.min !== "number" || typeof target.max !== "number") {
        return null;
      }
      if (value < target.min) return target.min - value;
      if (value > target.max) return value - target.max;
      return 0;
    case "upper_limit":
      if (typeof target.max !== "number") return null;
      return value <= target.max ? 0 : value - target.max;
    case "lower_limit":
      if (typeof target.min !== "number") return null;
      return value >= target.min ? 0 : target.min - value;
    default:
      return null;
  }
}

function targetProgress(measurement) {
  const currentDistance = targetDistance(measurement.value, measurement.target);
  const previousDistance = targetDistance(
    measurement.previous_value,
    measurement.target
  );

  if (currentDistance === null || previousDistance === null) return "neutral";

  const epsilon = 1e-9;
  if (currentDistance < previousDistance - epsilon) return "improved";
  if (currentDistance > previousDistance + epsilon) return "worsened";
  return "same";
}


function parseStoredReportDate(report) {
  const value = report?.sample_taken || report?.analysis_date;
  if (!value) return null;
  const normalized = value.includes("T") ? value : `${value}T12:00:00`;
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function historyDateLabel(value, language) {
  const parsed = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(parsed.getTime())) return "";
  return new Intl.DateTimeFormat(language === "de" ? "de-DE" : "en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(parsed);
}


function providerLabel(value) {
  if (!value) return "";
  if (value === "oceamo") return "Oceamo";
  if (value === "fauna_marin") return "Fauna Marin";
  if (value === "ati") return "ATI";
  if (value === "triton") return "TRITON";
  return String(value);
}

function supplySystemLabel(value, language) {
  if (!value) return "";
  const labels = {
    fauna_marin_balling_light: "Fauna Marin Balling Light",
    ati_essentials_pro: "ATI Essentials pro",
    triton_method: "TRITON Method",
    oceamo_duo: "Oceamo DUO",
  };
  if (value === "none") return TEXT[language].noSupplySystem;
  return labels[value] || String(value);
}


function stockingProfileLabel(value, language) {
  if (!value) return "";
  const labels = {
    de: {
      mixed_reef: "Mixed Reef",
      sps_dominant: "SPS-dominant",
      lps_dominant: "LPS-dominant",
      soft_coral_dominant: "Weichkorallen-dominant",
      fish_only: "Fish Only",
      other: "Sonstiges",
    },
    en: {
      mixed_reef: "Mixed Reef",
      sps_dominant: "SPS-dominant",
      lps_dominant: "LPS-dominant",
      soft_coral_dominant: "Soft-coral dominant",
      fish_only: "Fish Only",
      other: "Other",
    },
  };
  return labels[language]?.[value] || String(value);
}


function reportTypeLabel(value) {
  if (!value) return "";
  if (value === "reef_icp_ms") return "ICP-MS";
  if (value === "ultimate_ms") return "Ultimate-MS";
  if (value === "pro") return "Pro";
  if (value === "standard") return "Standard";
  if (value === "triton_legacy_icp") return "Legacy ICP-OES";
  return "";
}

function providerReportLabel(providerName, provider, reportType) {
  const lab = providerName || providerLabel(provider);
  const type = reportTypeLabel(reportType);
  return [lab, type].filter(Boolean).join(" · ");
}

function recommendationNumber(value, language, digits = 2) {
  if (typeof value !== "number" || Number.isNaN(value)) return "—";
  return numericLabel(value, language, digits);
}


function insightValue(value, rawValue, unit, language) {
  if (typeof value === "number" && !Number.isNaN(value)) {
    const suffix = unit ? ` ${unit}` : "";
    return `${numericLabel(value, language, 6)}${suffix}`;
  }
  if (rawValue !== null && rawValue !== undefined && String(rawValue).trim()) {
    const suffix = unit ? ` ${unit}` : "";
    return `${String(rawValue)}${suffix}`;
  }
  return "—";
}

function insightKindLabel(kind, t) {
  if (kind === "new_issue") return t.newIssue;
  if (kind === "resolved") return t.resolved;
  if (kind === "worsened") return t.statusWorsened;
  if (kind === "improved") return t.statusImproved;
  return kind || "";
}


function profileContextLabel(context, t) {
  if (context === "carbonate") return t.profileContextCarbonate;
  if (context === "nutrients") return t.profileContextNutrients;
  if (context === "salinity") return t.profileContextSalinity;
  return context || "";
}

function profileReason(item, profile, t) {
  if (item?.context === "carbonate") return t.profileReasonCarbonate;
  if (item?.context === "salinity") return t.profileReasonSalinity;
  if (item?.context === "nutrients") {
    if (profile === "sps_dominant") return t.profileReasonNutrientsSps;
    if (profile === "fish_only") return t.profileReasonNutrientsFish;
    return t.profileReasonNutrients;
  }
  return "";
}

function recommendationValue(item, field, language) {
  const value = item?.[field];
  if (typeof value !== "number") return "—";
  const unit = item?.unit ? ` ${item.unit}` : "";
  return `${numericLabel(value, language, 6)}${unit}`;
}


function recommendationKindLabel(item, t) {
  return item?.kind === "single_element" ? t.singleElement : t.coreCorrection;
}

function maintenanceText(code, t) {
  if (!code) return "";
  return t[`maintenance_${code}`] || "";
}

function interpolation(template, values) {
  return String(template || "").replace(/\{(\w+)\}/g, (_, key) =>
    key in values ? String(values[key]) : ""
  );
}

function safeExternalUrl(value) {
  try {
    const url = new URL(String(value || ""));
    return url.protocol === "https:" ? url.href : "";
  } catch (_error) {
    return "";
  }
}

function laboratoryRecommendationItem(measurement, language) {
  const t = TEXT[language];
  const recommendation = measurement?.recommendation;

  if (!recommendation || typeof recommendation !== "object") return "";

  const type = recommendation.type || "";
  const product =
    typeof recommendation.product === "string"
      ? recommendation.product.trim()
      : "";
  const name = measurement?.name || measurement?.key || "—";

  let body = "";
  let badge = t.laboratoryHintBadge;

  if (type === "water_change") {
    body = `
      <div class="recommendation-action">
        ${escapeHtml(t.laboratoryWaterChange)}
      </div>
    `;
  } else if (type === "dose") {
    badge = t.laboratoryDoseBadge;

    const amount =
      typeof recommendation.amount_ml === "number"
        ? recommendationNumber(recommendation.amount_ml, language, 3)
        : "";
    const days =
      Number.isInteger(recommendation.days) && recommendation.days > 0
        ? recommendation.days
        : null;
    const oneTime =
      typeof recommendation.one_time_ml === "number" &&
      recommendation.one_time_ml > 0
        ? recommendationNumber(recommendation.one_time_ml, language, 3)
        : "";
    const daily =
      typeof recommendation.daily_ml === "number" &&
      recommendation.daily_ml > 0
        ? recommendationNumber(recommendation.daily_ml, language, 3)
        : "";
    const reportVolume =
      typeof recommendation.aquarium_volume_l === "number" &&
      recommendation.aquarium_volume_l > 0
        ? recommendationNumber(recommendation.aquarium_volume_l, language, 1)
        : "";

    if (amount) {
      const dayLabel = days === 1 ? t.day : t.days;
      body += `
        <div class="recommendation-dose">
          <span>${escapeHtml(t.laboratoryDose)}</span>
          <strong>
            ${escapeHtml(amount)} ml${
              days ? ` · ${escapeHtml(days)} ${escapeHtml(dayLabel)}` : ""
            }
          </strong>
        </div>
      `;
    }

    if (oneTime) {
      body += `
        <div class="laboratory-dose-row">
          <span>${escapeHtml(t.laboratoryCorrection)}</span>
          <strong>${escapeHtml(oneTime)} ml</strong>
        </div>
      `;
    }

    if (daily) {
      body += `
        <div class="laboratory-dose-row">
          <span>${escapeHtml(t.laboratoryMaintenance)}</span>
          <strong>${escapeHtml(daily)} ml</strong>
        </div>
      `;
    }

    if (reportVolume) {
      body += `
        <div class="laboratory-report-volume">
          ${escapeHtml(t.laboratoryReportVolume)}:
          ${escapeHtml(reportVolume)} L
        </div>
      `;
    }
  }

  if (!body) return "";

  return `
    <div class="recommendation-item laboratory-recommendation-item">
      <div class="recommendation-item-head">
        <div>
          <span class="recommendation-kind">${escapeHtml(badge)}</span>
          <strong>${escapeHtml(name)}</strong>
        </div>
      </div>
      ${body}
      ${
        product
          ? `<div class="recommendation-product">${escapeHtml(product)}</div>`
          : ""
      }
    </div>
  `;
}


class ReefIcpHistoryCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = undefined;
    this._measurement = undefined;
    this._reports = [];
    this._language = "en";
    this._points = [];
    this._requestId = 0;
  }

  configure({ hass, measurement, reports, language }) {
    this._hass = hass;
    this._measurement = measurement;
    this._reports = Array.isArray(reports) ? reports : [];
    this._language = language || "en";
    this._points = [];
    this._load();
  }

  async _load() {
    const requestId = ++this._requestId;
    const t = TEXT[this._language];
    this._renderMessage("mdi:chart-line", t.loadingHistory, true);

    const statisticId = this._measurement?.historical_statistic_id;
    if (!this._hass?.callWS || !statisticId) {
      this._renderMessage("mdi:chart-line", t.noHistory);
      return;
    }

    const { start, end } = this._historyRange();

    try {
      const result = await this._hass.callWS({
        type: "recorder/statistics_during_period",
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        statistic_ids: [statisticId],
        period: "hour",
        types: ["mean"],
      });

      if (requestId !== this._requestId) return;

      const rawPoints = Array.isArray(result?.[statisticId])
        ? result[statisticId]
        : [];

      this._points = rawPoints
        .filter((point) => typeof point?.mean === "number")
        .map((point) => ({
          start: Number(point.start),
          value: Number(point.mean),
        }))
        .filter(
          (point) =>
            Number.isFinite(point.start) && Number.isFinite(point.value)
        )
        .sort((a, b) => a.start - b.start);

      this._render();
    } catch (error) {
      console.warn("Reef ICP history load failed", error);
      if (requestId !== this._requestId) return;
      this._renderMessage("mdi:alert-circle-outline", t.historyError);
    }
  }

  _historyRange() {
    const reportDates = this._reports
      .map(parseStoredReportDate)
      .filter((value) => value instanceof Date);

    if (!reportDates.length) {
      const end = new Date();
      const start = new Date(end);
      start.setFullYear(start.getFullYear() - 10);
      return { start, end };
    }

    const timestamps = reportDates.map((value) => value.getTime());
    const day = 24 * 60 * 60 * 1000;
    return {
      start: new Date(Math.min(...timestamps) - 2 * day),
      end: new Date(Math.max(...timestamps) + 2 * day),
    };
  }

  _reportForPoint(timestamp) {
    const day = 24 * 60 * 60 * 1000;
    let closest = null;
    let closestDistance = Infinity;

    for (const report of this._reports) {
      const date = parseStoredReportDate(report);
      if (!date) continue;
      const distance = Math.abs(date.getTime() - timestamp);
      if (distance < closestDistance && distance <= 2 * day) {
        closest = report;
        closestDistance = distance;
      }
    }
    return closest;
  }

  _summaryValue(value) {
    if (typeof value !== "number" || Number.isNaN(value)) return "—";
    const formatted = numericLabel(value, this._language);
    return this._measurement?.unit
      ? `${formatted} ${this._measurement.unit}`
      : formatted;
  }

  _changeValue() {
    const delta = this._measurement?.delta;
    if (typeof delta !== "number" || Number.isNaN(delta)) return "—";
    const sign = delta > 0 ? "+" : "";
    const formatted = numericLabel(delta, this._language);
    return this._measurement?.unit
      ? `${sign}${formatted} ${this._measurement.unit}`
      : `${sign}${formatted}`;
  }

  _targetGraphic(y, plotLeft, plotRight) {
    const target = this._measurement?.target;
    if (!target?.type) return "";

    const line = (value) => {
      if (typeof value !== "number") return "";
      const yPos = y(value);
      return `
        <line
          class="target-line"
          x1="${plotLeft}"
          y1="${yPos}"
          x2="${plotRight}"
          y2="${yPos}"
        ></line>
      `;
    };

    if (
      target.type === "range" &&
      typeof target.min === "number" &&
      typeof target.max === "number"
    ) {
      const top = y(target.max);
      const bottom = y(target.min);
      return `
        <rect
          class="target-band"
          x="${plotLeft}"
          y="${Math.min(top, bottom)}"
          width="${plotRight - plotLeft}"
          height="${Math.abs(bottom - top)}"
          rx="4"
        ></rect>
        ${line(target.min)}
        ${line(target.max)}
      `;
    }

    if (target.type === "exact") return line(target.value);
    if (target.type === "upper_limit") return line(target.max);
    if (target.type === "lower_limit") return line(target.min);
    return "";
  }

  _chart() {
    const points = this._points;
    if (!points.length) return "";

    const width = 640;
    const height = 270;
    const plotLeft = 56;
    const plotRight = width - 20;
    const plotTop = 18;
    const plotBottom = height - 46;

    const target = this._measurement?.target || {};
    const yValues = points.map((point) => point.value);
    for (const candidate of [target.value, target.min, target.max]) {
      if (typeof candidate === "number") yValues.push(candidate);
    }

    let yMin = Math.min(...yValues);
    let yMax = Math.max(...yValues);
    if (yMin === yMax) {
      const padding = Math.max(Math.abs(yMin) * 0.08, 1);
      yMin -= padding;
      yMax += padding;
    } else {
      const padding = (yMax - yMin) * 0.1;
      yMin -= padding;
      yMax += padding;
    }

    const xMin = points[0].start;
    const xMax = points[points.length - 1].start;
    const x = (timestamp) =>
      xMin === xMax
        ? (plotLeft + plotRight) / 2
        : plotLeft +
          ((timestamp - xMin) / (xMax - xMin)) * (plotRight - plotLeft);
    const y = (value) =>
      plotBottom -
      ((value - yMin) / (yMax - yMin)) * (plotBottom - plotTop);

    const path =
      points.length > 1
        ? points
            .map(
              (point, index) =>
                `${index === 0 ? "M" : "L"} ${x(point.start).toFixed(
                  2
                )} ${y(point.value).toFixed(2)}`
            )
            .join(" ")
        : "";

    const grid = Array.from({ length: 5 }, (_, index) => {
      const ratio = index / 4;
      const value = yMax - ratio * (yMax - yMin);
      const yPos = plotTop + ratio * (plotBottom - plotTop);
      return `
        <line
          class="grid-line"
          x1="${plotLeft}"
          y1="${yPos}"
          x2="${plotRight}"
          y2="${yPos}"
        ></line>
        <text class="axis-value" x="${plotLeft - 9}" y="${yPos + 4}">
          ${escapeHtml(numericLabel(value, this._language, 4))}
        </text>
      `;
    }).join("");

    const labelIndexes =
      points.length <= 4
        ? points.map((_, index) => index)
        : [0, Math.floor((points.length - 1) / 2), points.length - 1];

    const xLabels = [...new Set(labelIndexes)]
      .map((index) => {
        const point = points[index];
        return `
          <text
            class="axis-date"
            x="${x(point.start)}"
            y="${height - 17}"
            text-anchor="${
              index === 0
                ? "start"
                : index === points.length - 1
                  ? "end"
                  : "middle"
            }"
          >
            ${escapeHtml(historyDateLabel(point.start, this._language))}
          </text>
        `;
      })
      .join("");

    const circles = points
      .map((point, index) => {
        const report = this._reportForPoint(point.start);
        const analysis = report?.analysis_number
          ? ` · ${report.analysis_number}`
          : "";
        const provider = providerReportLabel(report?.provider_name, report?.provider, report?.report_type);
        const source = provider ? ` · ${provider}` : "";
        const title = `${historyDateLabel(
          point.start,
          this._language
        )}${analysis}${source} · ${this._summaryValue(point.value)}`;

        return `
          <circle
            class="chart-point${index === points.length - 1 ? " selected" : ""}"
            data-index="${index}"
            cx="${x(point.start)}"
            cy="${y(point.value)}"
            r="5.5"
            tabindex="0"
            role="button"
            aria-label="${escapeHtml(title)}"
          >
            <title>${escapeHtml(title)}</title>
          </circle>
        `;
      })
      .join("");

    return `
      <div class="chart-wrap">
        <svg
          class="history-chart"
          viewBox="0 0 ${width} ${height}"
          role="img"
          aria-label="${escapeHtml(this._measurement?.name || "")}"
        >
          ${grid}
          ${this._targetGraphic(y, plotLeft, plotRight)}
          ${
            path
              ? `<path class="history-line" d="${path}"></path>`
              : ""
          }
          ${circles}
          ${xLabels}
        </svg>
      </div>
    `;
  }

  _pointDetail(index) {
    const point = this._points[index];
    if (!point) return "";
    const report = this._reportForPoint(point.start);
    const analysis = report?.analysis_number || "";
    const provider = providerReportLabel(report?.provider_name, report?.provider, report?.report_type);
    const sourceLabel = [analysis, provider].filter(Boolean).join(" · ");
    return `
      <span>${escapeHtml(historyDateLabel(point.start, this._language))}</span>
      ${
        sourceLabel
          ? `<strong>${escapeHtml(sourceLabel)}</strong>`
          : ""
      }
      <strong>${escapeHtml(this._summaryValue(point.value))}</strong>
    `;
  }

  _wirePoints() {
    const points = this.shadowRoot?.querySelectorAll(".chart-point") || [];
    const select = (element) => {
      const index = Number(element.dataset.index);
      this.shadowRoot
        ?.querySelectorAll(".chart-point")
        .forEach((point) => point.classList.remove("selected"));
      element.classList.add("selected");
      const detail = this.shadowRoot?.querySelector(".point-detail");
      if (detail) detail.innerHTML = this._pointDetail(index);
    };

    points.forEach((element) => {
      element.addEventListener("click", () => select(element));
      element.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          select(element);
        }
      });
    });
  }

  _renderMessage(icon, message, loading = false) {
    this.shadowRoot.innerHTML = `
      <style>${this._styles()}</style>
      <div class="history-message">
        <ha-icon icon="${escapeHtml(icon)}" class="${loading ? "spin" : ""}"></ha-icon>
        <span>${escapeHtml(message)}</span>
      </div>
    `;
  }

  _render() {
    const t = TEXT[this._language];
    if (!this._points.length) {
      this._renderMessage("mdi:chart-line", t.noHistory);
      return;
    }

    const name = this._measurement?.name || this._measurement?.key || "—";
    const current = measurementValue(this._measurement || {}, this._language);
    const previous = this._measurement?.has_previous
      ? measurementValue(this._measurement, this._language, true)
      : "—";
    const target = targetLabel(this._measurement || {}, this._language);
    const latestPointIndex = this._points.length - 1;

    this.shadowRoot.innerHTML = `
      <style>${this._styles()}</style>
      <div class="history-card">
        <div class="history-heading">
          <div class="history-icon">
            <ha-icon icon="mdi:chart-line"></ha-icon>
          </div>
          <div class="history-heading-text">
            <div class="history-title">${escapeHtml(name)}</div>
            <div class="history-subtitle">
              ${escapeHtml(t.history)}
              · ${escapeHtml(this._points.length)} ${escapeHtml(t.analyses)}
            </div>
          </div>
        </div>

        <div class="history-summary">
          <div class="summary-item">
            <span>${escapeHtml(t.current)}</span>
            <strong>${escapeHtml(current)}</strong>
          </div>
          <div class="summary-item">
            <span>${escapeHtml(t.previous)}</span>
            <strong>${escapeHtml(previous)}</strong>
          </div>
          <div class="summary-item">
            <span>${escapeHtml(t.change)}</span>
            <strong>${escapeHtml(this._changeValue())}</strong>
          </div>
        </div>

        ${
          target
            ? `
              <div class="target-hint">
                <ha-icon icon="mdi:target"></ha-icon>
                <span>${escapeHtml(t.target)}: ${escapeHtml(target)}</span>
              </div>
            `
            : ""
        }

        ${this._chart()}

        <div class="point-detail" aria-live="polite">
          ${this._pointDetail(latestPointIndex)}
        </div>
      </div>
    `;

    this._wirePoints();
  }

  _styles() {
    return `
      :host {
        display: block;
        color: var(--primary-text-color);
      }

      .history-card {
        min-width: 0;
      }

      .history-heading {
        display: flex;
        align-items: center;
        gap: 11px;
        padding-right: 42px;
      }

      .history-icon {
        display: grid;
        place-items: center;
        width: 42px;
        height: 42px;
        flex: 0 0 auto;
        border-radius: 14px;
        color: var(--primary-color);
        background: color-mix(
          in srgb,
          var(--primary-color) 13%,
          transparent
        );
      }

      .history-heading-text {
        min-width: 0;
      }

      .history-title {
        overflow: hidden;
        color: var(--primary-text-color);
        font-size: 1.12rem;
        font-weight: 750;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .history-subtitle {
        margin-top: 3px;
        color: var(--secondary-text-color);
        font-size: 0.76rem;
      }

      .history-summary {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 7px;
        margin-top: 16px;
      }

      .summary-item {
        min-width: 0;
        padding: 9px 10px;
        border-radius: 12px;
        background: var(--secondary-background-color);
      }

      .summary-item span {
        display: block;
        color: var(--secondary-text-color);
        font-size: 0.67rem;
      }

      .summary-item strong {
        display: block;
        margin-top: 4px;
        overflow-wrap: anywhere;
        color: var(--primary-text-color);
        font-size: 0.8rem;
      }

      .target-hint {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-top: 11px;
        color: var(--secondary-text-color);
        font-size: 0.75rem;
      }

      .target-hint ha-icon {
        color: var(--primary-color);
        --mdc-icon-size: 16px;
      }

      .chart-wrap {
        margin-top: 8px;
        overflow: hidden;
        border-radius: 13px;
        background: color-mix(
          in srgb,
          var(--secondary-background-color) 56%,
          transparent
        );
      }

      .history-chart {
        display: block;
        width: 100%;
        height: auto;
        min-height: 210px;
        overflow: visible;
      }

      .grid-line {
        stroke: var(--divider-color);
        stroke-width: 1;
      }

      .axis-value,
      .axis-date {
        fill: var(--secondary-text-color);
        font-family: sans-serif;
        font-size: 10px;
      }

      .history-line {
        fill: none;
        stroke: var(--primary-color);
        stroke-linecap: round;
        stroke-linejoin: round;
        stroke-width: 3;
      }

      .target-band {
        fill: var(--success-color, #43a047);
        opacity: 0.1;
      }

      .target-line {
        stroke: var(--success-color, #43a047);
        stroke-dasharray: 5 5;
        stroke-width: 1.4;
        opacity: 0.75;
      }

      .chart-point {
        cursor: pointer;
        fill: var(--ha-card-background, var(--card-background-color));
        stroke: var(--primary-color);
        stroke-width: 3;
        transition:
          r 120ms ease,
          stroke-width 120ms ease;
      }

      .chart-point.selected {
        r: 7;
        stroke-width: 4;
      }

      .chart-point:focus-visible {
        outline: none;
        stroke: var(--primary-text-color);
      }

      .point-detail {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 5px 12px;
        min-height: 22px;
        margin-top: 8px;
        color: var(--secondary-text-color);
        font-size: 0.74rem;
      }

      .point-detail strong {
        color: var(--primary-text-color);
        font-weight: 650;
      }

      .history-message {
        display: flex;
        min-height: 180px;
        align-items: center;
        justify-content: center;
        gap: 10px;
        color: var(--secondary-text-color);
        text-align: center;
      }

      .history-message ha-icon {
        color: var(--primary-color);
      }

      .spin {
        animation: reef-history-spin 1s linear infinite;
      }

      @keyframes reef-history-spin {
        to {
          transform: rotate(360deg);
        }
      }

      @media (max-width: 520px) {
        .history-summary {
          gap: 5px;
        }

        .summary-item {
          padding: 8px 7px;
        }

        .summary-item span {
          font-size: 0.62rem;
        }

        .summary-item strong {
          font-size: 0.73rem;
        }

        .history-chart {
          min-height: 190px;
        }
      }

      @media (prefers-reduced-motion: reduce) {
        .spin {
          animation: none;
        }
      }
    `;
  }
}

if (!customElements.get(HISTORY_CARD_TAG)) {
  customElements.define(HISTORY_CARD_TAG, ReefIcpHistoryCard);
}

class ReefIcpCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = undefined;
    this._lastState = undefined;
    this._openCategories = null;
  }

  static getConfigForm() {
    const documentLanguage =
      document.documentElement.lang || navigator.language || "en";
    const language = documentLanguage.toLowerCase().startsWith("de")
      ? "de"
      : "en";
    const t = TEXT[language];

    return {
      schema: [
        {
          name: "entity",
          required: true,
          selector: {
            entity: {
              filter: {
                domain: "sensor",
              },
            },
          },
        },
        {
          name: "title",
          selector: {
            text: {},
          },
        },
        {
          name: "show_previous",
          selector: {
            boolean: {},
          },
        },
      ],
      computeLabel: (schema) => {
        if (schema.name === "entity") return t.entity;
        if (schema.name === "title") return t.title;
        if (schema.name === "show_previous") return t.showPrevious;
        return undefined;
      },
    };
  }

  static getStubConfig(hass) {
    const state = Object.values(hass?.states || {}).find((candidate) => {
      const attrs = candidate?.attributes || {};
      return (
        candidate.entity_id?.startsWith("sensor.") &&
        Array.isArray(attrs.measurements) &&
        "analysis_number" in attrs &&
        "status_counts" in attrs
      );
    });

    return {
      entity: state?.entity_id || "",
      show_previous: true,
    };
  }

  setConfig(config) {
    this._config = {
      show_previous: true,
      ...config,
    };
    this._lastState = undefined;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    const state = this._config.entity
      ? hass?.states?.[this._config.entity]
      : undefined;

    if (state !== this._lastState) {
      this._lastState = state;
      this._render();
    }
  }

  getCardSize() {
    const measurements =
      this._lastState?.attributes?.measurements?.length || 0;
    return Math.max(4, Math.ceil(measurements / 5) + 3);
  }

  getGridOptions() {
    return {
      columns: 12,
      min_columns: 6,
    };
  }

  _wireCategoryToggles() {
    this.shadowRoot?.querySelectorAll("details.category").forEach((details) => {
      details.addEventListener("toggle", () => {
        if (this._openCategories === null) this._openCategories = new Set();
        if (details.open) {
          this._openCategories.add(details.dataset.category);
        } else {
          this._openCategories.delete(details.dataset.category);
        }
      });
    });
  }

  _isCategoryOpen(category, index, hasBasic) {
    if (this._openCategories !== null) {
      return this._openCategories.has(category);
    }
    return category === "basic" || (index === 0 && !hasBasic);
  }

  _render() {
    if (!this.shadowRoot) return;

    const language = languageFor(this._hass);
    const t = TEXT[language];

    if (!this._config.entity) {
      this.shadowRoot.innerHTML = this._messageCard(t.cardName, t.noEntity);
      return;
    }

    const state = this._hass?.states?.[this._config.entity];
    if (!state) {
      this.shadowRoot.innerHTML = this._messageCard(
        t.cardName,
        t.entityMissing
      );
      return;
    }

    const attrs = state.attributes || {};
    const measurements = Array.isArray(attrs.measurements)
      ? attrs.measurements
      : [];

    if (!measurements.length) {
      this.shadowRoot.innerHTML = this._messageCard(
        t.cardName,
        t.invalidEntity
      );
      return;
    }

    const friendlyName =
      attrs.friendly_name || this._config.entity || t.cardName;
    const inferredTitle = friendlyName.replace(/\s+ICP Status$/i, "");
    const title = this._config.title?.trim() || inferredTitle || t.cardName;
    const analysisNumber = attrs.analysis_number || "—";
    const analysisDate = dateLabel(attrs.analysis_date, language);
    const providerName = providerReportLabel(attrs.provider_name, attrs.provider, attrs.report_type);
    const counts = attrs.status_counts || {};
    const overall = state.state || "unknown";
    const previousAnalysis = attrs.previous_analysis_number;
    const previousDate = dateLabel(attrs.previous_analysis_date, language);
    const previousProvider = providerReportLabel(
      attrs.previous_provider_name,
      attrs.previous_provider,
      attrs.previous_report_type
    );
    const aquariumVolume = Number(attrs.aquarium_volume_l);
    const hasAquariumVolume =
      Number.isFinite(aquariumVolume) && aquariumVolume > 0;
    const stockingProfile = stockingProfileLabel(
      attrs.stocking_profile,
      language
    );
    const supplySystem = supplySystemLabel(attrs.supply_system, language);
    const interpretation =
      typeof attrs.interpretation === "string"
        ? attrs.interpretation.trim()
        : "";
    const explicitLaboratoryRecommendations =
      attrs.laboratory_recommendations &&
      typeof attrs.laboratory_recommendations === "object"
        ? attrs.laboratory_recommendations
        : null;
    const productRecommendations =
      typeof explicitLaboratoryRecommendations?.report_text === "string"
        ? explicitLaboratoryRecommendations.report_text.trim()
        : typeof attrs.product_recommendations === "string"
          ? attrs.product_recommendations.trim()
          : "";
    const explicitLaboratoryItems = Array.isArray(
      explicitLaboratoryRecommendations?.items
    )
      ? explicitLaboratoryRecommendations.items
      : [];
    const fallbackLaboratoryItems = measurements
      .filter(
        (measurement) =>
          measurement?.recommendation &&
          typeof measurement.recommendation === "object"
      )
      .map((measurement) => ({
        ...measurement,
        recommendation: measurement.recommendation,
      }));
    const laboratoryRecommendationItems =
      explicitLaboratoryItems.length > 0
        ? explicitLaboratoryItems
        : fallbackLaboratoryItems;
    const hasLaboratoryRecommendations =
      laboratoryRecommendationItems.length > 0 ||
      Boolean(productRecommendations);
    const laboratoryProvider =
      explicitLaboratoryRecommendations?.provider_name ||
      attrs.provider_name ||
      providerLabel(attrs.provider) ||
      t.cardName;
    const supplyRecommendations =
      attrs.supply_recommendations &&
      typeof attrs.supply_recommendations === "object"
        ? attrs.supply_recommendations
        : null;
    const analysisInsights =
      attrs.analysis_insights &&
      typeof attrs.analysis_insights === "object"
        ? attrs.analysis_insights
        : null;
    const insightChanges = Array.isArray(analysisInsights?.changes)
      ? analysisInsights.changes
      : [];
    const insightTrends = Array.isArray(analysisInsights?.trends)
      ? analysisInsights.trends
      : [];
    const insightComparedTo = analysisInsights?.compared_to || null;
    const stockingProfileInsights =
      attrs.stocking_profile_insights &&
      typeof attrs.stocking_profile_insights === "object"
        ? attrs.stocking_profile_insights
        : null;
    const profileInsightItems = Array.isArray(
      stockingProfileInsights?.items
    )
      ? stockingProfileInsights.items
      : [];

    const grouped = new Map();
    for (const measurement of measurements) {
      const category = measurement.category || "unknown";
      if (!grouped.has(category)) grouped.set(category, []);
      grouped.get(category).push(measurement);
    }

    const categories = [
      ...CATEGORY_ORDER.filter((key) => grouped.has(key)),
      ...[...grouped.keys()].filter((key) => !CATEGORY_ORDER.includes(key)),
    ];

    this.shadowRoot.innerHTML = `
      <style>${this._styles()}</style>
      <ha-card>
        <div class="header">
          <div class="title-row">
            <div class="brand-icon">
              <ha-icon icon="mdi:test-tube"></ha-icon>
            </div>
            <div class="title-wrap">
              <div class="title">${escapeHtml(title)}</div>
              <div class="meta">
                ${escapeHtml(analysisNumber)}
                ${analysisDate ? ` · ${escapeHtml(analysisDate)}` : ""}
                ${providerName ? ` · ${escapeHtml(providerName)}` : ""}
              </div>
            </div>
            <div class="overall ${escapeHtml(overall)}">
              ${escapeHtml(this._overallLabel(overall, language))}
            </div>
          </div>

          <div class="status-strip">
            ${this._statusCount("ok", counts.ok || 0, t.okShort)}
            ${this._statusCount(
              "warning",
              counts.warning || 0,
              t.warningShort
            )}
            ${this._statusCount(
              "critical",
              counts.critical || 0,
              t.criticalShort
            )}
            ${
              counts.unknown
                ? this._statusCount(
                    "unknown",
                    counts.unknown || 0,
                    t.unknownShort
                  )
                : ""
            }
          </div>

          ${
            previousAnalysis && this._config.show_previous !== false
              ? `
                <div class="previous-analysis">
                  <ha-icon icon="mdi:history"></ha-icon>
                  <span>${escapeHtml(t.previous)}</span>
                  <strong>${escapeHtml(previousAnalysis)}</strong>
                  ${
                    previousDate
                      ? `<span class="previous-date">· ${escapeHtml(
                          previousDate
                        )}</span>`
                      : ""
                  }
                  ${
                    previousProvider
                      ? `<span class="previous-date">· ${escapeHtml(
                          previousProvider
                        )}</span>`
                      : ""
                  }
                </div>
              `
              : ""
          }

          ${
            hasAquariumVolume || stockingProfile || supplySystem
              ? `
                <div class="aquarium-profile">
                  ${
                    hasAquariumVolume
                      ? `
                        <span class="profile-chip">
                          <ha-icon icon="mdi:waves"></ha-icon>
                          <strong>${escapeHtml(t.netVolume)}:</strong>
                          ${escapeHtml(numericLabel(aquariumVolume, language, 1))} L
                        </span>
                      `
                      : ""
                  }
                  ${
                    stockingProfile
                      ? `
                        <span class="profile-chip">
                          <ha-icon icon="mdi:fishbowl-outline"></ha-icon>
                          ${escapeHtml(stockingProfile)}
                        </span>
                      `
                      : ""
                  }
                  ${
                    supplySystem
                      ? `
                        <span class="profile-chip">
                          <ha-icon icon="mdi:flask-outline"></ha-icon>
                          ${escapeHtml(supplySystem)}
                        </span>
                      `
                      : ""
                  }
                </div>
              `
              : ""
          }
        </div>

        <div class="categories">
          ${categories
            .map((category, index) =>
              this._category(
                category,
                grouped.get(category),
                language,
                this._isCategoryOpen(category, index, grouped.has("basic"))
              )
            )
            .join("")}
        </div>

        ${
          analysisInsights && insightComparedTo
            ? `
              <details class="info-panel insights-panel">
                <summary class="info-summary">
                  <span class="info-icon">
                    <ha-icon icon="mdi:chart-timeline-variant-shimmer"></ha-icon>
                  </span>
                  <strong>${escapeHtml(t.changesSinceLast)}</strong>
                  <ha-icon class="info-chevron" icon="mdi:chevron-down"></ha-icon>
                </summary>
                <div class="info-content insight-content">
                  <div class="insight-comparison">
                    ${escapeHtml(t.comparedWith)}
                    <strong>${escapeHtml(
                      insightComparedTo.analysis_number || "—"
                    )}</strong>
                    ${
                      insightComparedTo.analysis_date
                        ? ` · ${escapeHtml(
                            dateLabel(
                              insightComparedTo.analysis_date,
                              language
                            )
                          )}`
                        : ""
                    }
                    ${
                      insightComparedTo.provider_name ||
                      insightComparedTo.provider
                        ? ` · ${escapeHtml(
                            providerReportLabel(
                              insightComparedTo.provider_name,
                              insightComparedTo.provider,
                              insightComparedTo.report_type
                            )
                          )}`
                        : ""
                    }
                  </div>

                  ${
                    insightChanges.length
                      ? `
                        <div class="insight-list">
                          ${insightChanges
                            .map((item) => {
                              const previousValue = insightValue(
                                item.previous,
                                item.previous_raw_value,
                                item.unit,
                                language
                              );
                              const currentValue = insightValue(
                                item.current,
                                item.current_raw_value,
                                item.unit,
                                language
                              );
                              return `
                                <div class="insight-item ${escapeHtml(
                                  item.kind || ""
                                )}">
                                  <div class="insight-item-head">
                                    <strong>${escapeHtml(
                                      item.name || item.key || "—"
                                    )}</strong>
                                    <span class="insight-badge ${escapeHtml(
                                      item.kind || ""
                                    )}">
                                      ${escapeHtml(
                                        insightKindLabel(item.kind, t)
                                      )}
                                    </span>
                                  </div>
                                  <div class="insight-values">
                                    ${escapeHtml(previousValue)}
                                    <ha-icon icon="mdi:arrow-right"></ha-icon>
                                    <strong>${escapeHtml(currentValue)}</strong>
                                  </div>
                                </div>
                              `;
                            })
                            .join("")}
                        </div>
                      `
                      : `
                        <div class="recommendation-empty">
                          ${escapeHtml(t.noStatusChanges)}
                        </div>
                      `
                  }

                  ${
                    insightTrends.length
                      ? `
                        <div class="insight-trend-title">
                          <ha-icon icon="mdi:trending-up"></ha-icon>
                          <strong>${escapeHtml(t.repeatedTrends)}</strong>
                        </div>
                        <div class="insight-trend-list">
                          ${insightTrends
                            .map((item) => {
                              const directionText = interpolation(
                                item.direction === "down"
                                  ? t.trendDown
                                  : t.trendUp,
                                { count: item.measurement_count || 0 }
                              );
                              const fromValue = insightValue(
                                item.first_value,
                                null,
                                item.unit,
                                language
                              );
                              const toValue = insightValue(
                                item.current_value,
                                null,
                                item.unit,
                                language
                              );
                              const fromTo = interpolation(t.trendFromTo, {
                                from: fromValue,
                                to: toValue,
                              });
                              return `
                                <div class="insight-trend-item">
                                  <span class="insight-trend-icon ${escapeHtml(
                                    item.direction || ""
                                  )}">
                                    <ha-icon icon="${
                                      item.direction === "down"
                                        ? "mdi:trending-down"
                                        : "mdi:trending-up"
                                    }"></ha-icon>
                                  </span>
                                  <div>
                                    <strong>${escapeHtml(
                                      item.name || item.key || "—"
                                    )}</strong>
                                    <span>${escapeHtml(directionText)}</span>
                                    <small>${escapeHtml(fromTo)}</small>
                                  </div>
                                </div>
                              `;
                            })
                            .join("")}
                        </div>
                        ${
                          analysisInsights.trend_items_limited
                            ? `
                              <div class="insight-more">
                                ${escapeHtml(
                                  interpolation(t.trendMore, {
                                    count: Math.max(
                                      0,
                                      Number(analysisInsights.trend_count || 0) -
                                        insightTrends.length
                                    ),
                                  })
                                )}
                              </div>
                            `
                            : ""
                        }
                        <div class="recommendation-note insight-note">
                          <ha-icon icon="mdi:information-outline"></ha-icon>
                          <span>${escapeHtml(t.trendNote)}</span>
                        </div>
                      `
                      : ""
                  }
                </div>
              </details>
            `
            : ""
        }

        ${
          stockingProfileInsights && profileInsightItems.length
            ? `
              <details class="info-panel profile-insights-panel">
                <summary class="info-summary">
                  <span class="info-icon">
                    <ha-icon icon="mdi:fishbowl-outline"></ha-icon>
                  </span>
                  <strong>${escapeHtml(t.profileInsights)}</strong>
                  <ha-icon class="info-chevron" icon="mdi:chevron-down"></ha-icon>
                </summary>
                <div class="info-content profile-insight-content">
                  <div class="recommendation-system">
                    ${escapeHtml(
                      interpolation(t.profileContextFor, {
                        profile:
                          stockingProfileLabel(
                            stockingProfileInsights.profile,
                            language
                          ) ||
                          stockingProfileInsights.profile_name ||
                          "—",
                      })
                    )}
                  </div>

                  <div class="profile-insight-list">
                    ${profileInsightItems
                      .map((item) => {
                        const currentValue = insightValue(
                          item.current,
                          item.current_raw_value,
                          item.unit,
                          language
                        );
                        const attention =
                          item.attention === "high"
                            ? t.profileHigh
                            : t.profileMedium;
                        const contextLabel = profileContextLabel(
                          item.context,
                          t
                        );
                        const reason = profileReason(
                          item,
                          stockingProfileInsights.profile,
                          t
                        );
                        const trendText = item.trend_direction
                          ? interpolation(
                              item.trend_direction === "down"
                                ? t.profileTrendDown
                                : t.profileTrendUp,
                              {
                                count:
                                  item.trend_measurement_count || 0,
                              }
                            )
                          : "";
                        return `
                          <div class="profile-insight-item">
                            <div class="profile-insight-head">
                              <div>
                                <span class="profile-context-label">
                                  ${escapeHtml(contextLabel)}
                                </span>
                                <strong>${escapeHtml(
                                  item.name || item.key || "—"
                                )}</strong>
                              </div>
                              <span class="profile-attention ${escapeHtml(
                                item.attention || "medium"
                              )}">
                                ${escapeHtml(attention)}
                              </span>
                            </div>

                            <div class="profile-insight-value">
                              ${escapeHtml(currentValue)}
                            </div>

                            ${
                              item.current_issue
                                ? `
                                  <div class="profile-signal">
                                    <ha-icon icon="mdi:alert-circle-outline"></ha-icon>
                                    <span>${escapeHtml(
                                      t.profileCurrentIssue
                                    )}</span>
                                  </div>
                                `
                                : ""
                            }

                            ${
                              trendText
                                ? `
                                  <div class="profile-signal">
                                    <ha-icon icon="${
                                      item.trend_direction === "down"
                                        ? "mdi:trending-down"
                                        : "mdi:trending-up"
                                    }"></ha-icon>
                                    <span>${escapeHtml(trendText)}</span>
                                  </div>
                                `
                                : ""
                            }

                            ${
                              reason
                                ? `
                                  <div class="profile-reason">
                                    ${escapeHtml(reason)}
                                  </div>
                                `
                                : ""
                            }
                          </div>
                        `;
                      })
                      .join("")}
                  </div>

                  ${
                    stockingProfileInsights.items_limited
                      ? `
                        <div class="insight-more">
                          ${escapeHtml(
                            interpolation(t.profileMore, {
                              count: Math.max(
                                0,
                                Number(
                                  stockingProfileInsights.item_count || 0
                                ) - profileInsightItems.length
                              ),
                            })
                          )}
                        </div>
                      `
                      : ""
                  }

                  <div class="recommendation-note profile-basis-note">
                    <ha-icon icon="mdi:information-outline"></ha-icon>
                    <span>${escapeHtml(t.profileBasisNote)}</span>
                  </div>
                </div>
              </details>
            `
            : ""
        }

        ${
          hasLaboratoryRecommendations
            ? `
              <details class="info-panel laboratory-panel">
                <summary class="info-summary">
                  <span class="info-icon">
                    <ha-icon icon="mdi:file-document-check-outline"></ha-icon>
                  </span>
                  <strong>${escapeHtml(t.laboratoryRecommendations)}</strong>
                  <ha-icon class="info-chevron" icon="mdi:chevron-down"></ha-icon>
                </summary>
                <div class="info-content recommendation-content">
                  <div class="recommendation-system">
                    ${escapeHtml(
                      interpolation(t.laboratoryFromReport, {
                        provider: laboratoryProvider,
                      })
                    )}
                  </div>

                  ${
                    laboratoryRecommendationItems.length
                      ? `
                        <div class="recommendation-list">
                          ${laboratoryRecommendationItems
                            .map((measurement) =>
                              laboratoryRecommendationItem(
                                measurement,
                                language
                              )
                            )
                            .filter(Boolean)
                            .join("")}
                        </div>
                      `
                      : ""
                  }

                  ${
                    productRecommendations
                      ? `
                        <div class="laboratory-report-text">
                          <strong>${escapeHtml(
                            t.laboratoryAdditionalText
                          )}</strong>
                          <div>${escapeHtml(productRecommendations)}</div>
                        </div>
                      `
                      : ""
                  }

                  <div class="recommendation-note laboratory-source-note">
                    <ha-icon icon="mdi:file-document-outline"></ha-icon>
                    <span>${escapeHtml(t.laboratorySourceNote)}</span>
                  </div>
                </div>
              </details>
            `
            : ""
        }

        ${
          supplyRecommendations
            ? `
              <details class="info-panel recommendation-panel">
                <summary class="info-summary">
                  <span class="info-icon">
                    <ha-icon icon="mdi:flask-round-bottom"></ha-icon>
                  </span>
                  <strong>${escapeHtml(t.supplyRecommendations)}</strong>
                  <ha-icon class="info-chevron" icon="mdi:chevron-down"></ha-icon>
                </summary>
                <div class="info-content recommendation-content">
                  <div class="recommendation-system">
                    ${escapeHtml(
                      supplyRecommendations.system_name ||
                        supplySystem ||
                        ""
                    )}
                    ${
                      supplyRecommendations.volume_l
                        ? ` · ${escapeHtml(
                            numericLabel(
                              Number(supplyRecommendations.volume_l),
                              language,
                              1
                            )
                          )} L`
                        : ""
                    }
                  </div>

                  ${
                    supplyRecommendations.supported
                      ? `
                        ${
                          Array.isArray(supplyRecommendations.items) &&
                          supplyRecommendations.items.length
                            ? `
                              <div class="recommendation-list">
                                ${supplyRecommendations.items
                                  .map((item) => {
                                    const sourceUrl = safeExternalUrl(
                                      item.source_url
                                    );
                                    const doseUnit =
                                      item.dose_unit || "ml";
                                    const doseAmount =
                                      typeof item.dose_amount === "number"
                                        ? recommendationNumber(
                                            item.dose_amount,
                                            language,
                                            3
                                          )
                                        : "";
                                    const dailyDose =
                                      typeof item.daily_dose_amount === "number"
                                        ? recommendationNumber(
                                            item.daily_dose_amount,
                                            language,
                                            3
                                          )
                                        : "";
                                    const splitText =
                                      item.split_days > 1 &&
                                      dailyDose
                                        ? interpolation(t.splitDose, {
                                            days: item.split_days,
                                            dose: dailyDose,
                                            unit: doseUnit,
                                          })
                                        : "";
                                    const dailyIncrease =
                                      splitText &&
                                      typeof item.delta === "number" &&
                                      item.split_days > 0
                                        ? interpolation(t.dailyIncrease, {
                                            amount: recommendationNumber(
                                              item.delta / item.split_days,
                                              language,
                                              3
                                            ),
                                            unit: item.unit || "",
                                          })
                                        : "";
                                    const smallDose =
                                      item.action === "correction_dose" &&
                                      doseUnit.toLowerCase() === "ml" &&
                                      typeof item.dose_amount === "number" &&
                                      item.dose_amount > 0 &&
                                      (item.daily_dose_amount || item.dose_amount) < 1;

                                    return `
                                      <div class="recommendation-item">
                                        <div class="recommendation-item-head">
                                          <div>
                                            <span class="recommendation-kind">
                                              ${escapeHtml(
                                                recommendationKindLabel(
                                                  item,
                                                  t
                                                )
                                              )}
                                            </span>
                                            <strong>${escapeHtml(
                                              item.name || item.key || "—"
                                            )}</strong>
                                          </div>
                                          ${
                                            item.action === "requires_icp_ms"
                                              ? ""
                                              : `
                                                <span class="recommendation-values">
                                                  ${escapeHtml(
                                                    recommendationValue(
                                                      item,
                                                      "current",
                                                      language
                                                    )
                                                  )}
                                                  →
                                                  ${escapeHtml(
                                                    recommendationValue(
                                                      item,
                                                      "target",
                                                      language
                                                    )
                                                  )}
                                                </span>
                                              `
                                          }
                                        </div>

                                        ${
                                          item.action === "correction_dose"
                                            ? `
                                              <div class="recommendation-dose">
                                                <span>${escapeHtml(
                                                  t.correctionDose
                                                )}</span>
                                                <strong>${escapeHtml(
                                                  doseAmount
                                                )} ${escapeHtml(
                                                  doseUnit
                                                )}</strong>
                                              </div>
                                              ${
                                                splitText
                                                  ? `
                                                    <div class="recommendation-schedule">
                                                      <ha-icon icon="mdi:calendar-clock-outline"></ha-icon>
                                                      <span>${escapeHtml(
                                                        splitText
                                                      )}<br>${escapeHtml(
                                                        dailyIncrease
                                                      )}</span>
                                                    </div>
                                                  `
                                                  : item.daily_limit_known === false
                                                    ? `
                                                      <div class="recommendation-warning">
                                                        <ha-icon icon="mdi:alert-outline"></ha-icon>
                                                        <span>${escapeHtml(
                                                          t.dailyLimitUnknown
                                                        )}</span>
                                                      </div>
                                                    `
                                                    : ""
                                              }
                                              ${
                                                smallDose
                                                  ? `<div class="recommendation-warning">
                                                       <ha-icon icon="mdi:eyedropper"></ha-icon>
                                                       <span>${escapeHtml(t.smallDose)}</span>
                                                     </div>`
                                                  : ""
                                              }
                                            `
                                            : item.action ===
                                                "official_calculator"
                                              ? `
                                                <div class="recommendation-action">
                                                  ${escapeHtml(
                                                    t.officialCalculator
                                                  )}
                                                </div>
                                              `
                                              : item.action ===
                                                  "requires_icp_ms"
                                                ? `
                                                  <div class="recommendation-warning">
                                                    <ha-icon icon="mdi:microscope"></ha-icon>
                                                    <span>${escapeHtml(
                                                      t.requiresIcpMs
                                                    )}</span>
                                                  </div>
                                                `
                                                : `
                                                  <div class="recommendation-action">
                                                    ${escapeHtml(
                                                      t.reduceOrPause
                                                    )}
                                                  </div>
                                                `
                                        }

                                        <div class="recommendation-product">
                                          ${escapeHtml(
                                            item.product || ""
                                          )}
                                          ${
                                            item.solution
                                              ? ` · ${escapeHtml(
                                                  item.solution
                                                )}`
                                              : ""
                                          }
                                        </div>

                                        ${
                                          sourceUrl
                                            ? `
                                              <a
                                                class="recommendation-source"
                                                href="${escapeHtml(sourceUrl)}"
                                                target="_blank"
                                                rel="noopener noreferrer"
                                              >
                                                <ha-icon icon="mdi:open-in-new"></ha-icon>
                                                ${escapeHtml(
                                                  item.source_name ||
                                                    t.openManufacturer
                                                )}
                                              </a>
                                            `
                                            : ""
                                        }
                                      </div>
                                    `;
                                  })
                                  .join("")}
                              </div>
                            `
                            : `
                              <div class="recommendation-empty">
                                ${escapeHtml(t.noCorrection)}
                              </div>
                            `
                        }

                        ${
                          maintenanceText(
                            supplyRecommendations.maintenance_note,
                            t
                          )
                            ? `
                              <div class="recommendation-note">
                                <ha-icon icon="mdi:chart-timeline-variant"></ha-icon>
                                <span>${escapeHtml(
                                  maintenanceText(
                                    supplyRecommendations.maintenance_note,
                                    t
                                  )
                                )}</span>
                              </div>
                            `
                            : ""
                        }

                        <div class="recommendation-note">
                          <ha-icon icon="mdi:information-outline"></ha-icon>
                          <span>${escapeHtml(t.correctionOnly)}</span>
                        </div>
                      `
                      : `
                        <div class="recommendation-empty">
                          ${escapeHtml(t.recommendationUnavailable)}
                        </div>
                      `
                  }
                </div>
              </details>
            `
            : ""
        }

        ${
          interpretation
            ? `
              <details class="info-panel interpretation-panel">
                <summary class="info-summary">
                  <span class="info-icon">
                    <ha-icon icon="mdi:text-box-search-outline"></ha-icon>
                  </span>
                  <strong>${escapeHtml(t.interpretation)}</strong>
                  <ha-icon class="info-chevron" icon="mdi:chevron-down"></ha-icon>
                </summary>
                <div class="interpretation-text info-content">
                  ${escapeHtml(interpretation)}
                </div>
              </details>
            `
            : ""
        }

        <dialog class="history-dialog">
          <div class="history-dialog-inner">
            <button
              class="history-close"
              type="button"
              title="${escapeHtml(t.close)}"
              aria-label="${escapeHtml(t.close)}"
            >
              <ha-icon icon="mdi:close"></ha-icon>
            </button>
            <${HISTORY_CARD_TAG}></${HISTORY_CARD_TAG}>
          </div>
        </dialog>
      </ha-card>
    `;

    this._wireCategoryToggles();
    this._wireHistoryInteractions();
  }

  _wireHistoryInteractions() {
    const dialog = this.shadowRoot?.querySelector(".history-dialog");
    const close = this.shadowRoot?.querySelector(".history-close");

    close?.addEventListener("click", () => dialog?.close());
    dialog?.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });

    const open = (row) => {
      const category = row.dataset.category;
      const key = row.dataset.key;
      const state = this._hass?.states?.[this._config.entity];
      const attrs = state?.attributes || {};
      const measurement = (attrs.measurements || []).find(
        (item) => item.category === category && item.key === key
      );

      if (!measurement?.historical_statistic_id || !dialog) return;

      const historyCard = dialog.querySelector(HISTORY_CARD_TAG);
      historyCard?.configure({
        hass: this._hass,
        measurement,
        reports: attrs.stored_reports || [],
        language: languageFor(this._hass),
      });
      dialog.showModal();
    };

    this.shadowRoot
      ?.querySelectorAll(".measurement.history-enabled")
      .forEach((row) => {
        row.addEventListener("click", () => open(row));
        row.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            open(row);
          }
        });
      });
  }

  _messageCard(title, message) {
    return `
      <style>${this._styles()}</style>
      <ha-card>
        <div class="message">
          <ha-icon icon="mdi:test-tube"></ha-icon>
          <div>
            <div class="message-title">${escapeHtml(title)}</div>
            <div class="message-text">${escapeHtml(message)}</div>
          </div>
        </div>
      </ha-card>
    `;
  }

  _overallLabel(status, language) {
    const t = TEXT[language];
    if (status === "ok") return t.ok;
    if (status === "warning") return t.warning;
    if (status === "critical") return t.critical;
    return t.statusUnknown;
  }

  _statusCount(status, count, label) {
    return `
      <div class="status-count ${status}">
        <span class="status-dot"></span>
        <span class="status-label">${escapeHtml(label)}</span>
        <strong>${escapeHtml(count)}</strong>
      </div>
    `;
  }

  _measurementCountLabel(count, language) {
    const t = TEXT[language];
    return `${count} ${count === 1 ? t.measurement : t.measurements}`;
  }

  _categoryStatusCounts(measurements) {
    const counts = {
      ok: 0,
      warning: 0,
      critical: 0,
      unknown: 0,
    };

    for (const measurement of measurements) {
      const severity = measurement?.status?.severity || "unknown";
      if (severity in counts) {
        counts[severity] += 1;
      } else {
        counts.unknown += 1;
      }
    }

    return counts;
  }

  _categoryStatusSummary(counts, language) {
    const t = TEXT[language];
    const items = [
      ["ok", counts.ok, t.okShort],
      ["warning", counts.warning, t.warningShort],
      ["critical", counts.critical, t.criticalShort],
      ["unknown", counts.unknown, t.unknownShort],
    ].filter(([, count]) => count > 0);

    return `
      <span class="category-status" aria-label="${escapeHtml(
        items.map(([, count, label]) => `${label}: ${count}`).join(", ")
      )}">
        ${items
          .map(
            ([status, count, label]) => `
              <span
                class="category-status-item ${escapeHtml(status)}"
                title="${escapeHtml(`${label}: ${count}`)}"
              >
                <span class="status-dot"></span>
                <span class="category-status-count">${escapeHtml(count)}</span>
              </span>
            `
          )
          .join("")}
      </span>
    `;
  }

  _category(category, measurements, language, isOpen) {
    const t = TEXT[language];
    const label = t.categories[category] || t.categories.unknown;
    const icon = CATEGORY_ICONS[category] || "mdi:flask-outline";
    const statusCounts = this._categoryStatusCounts(measurements);
    const countLabel = this._measurementCountLabel(
      measurements.length,
      language
    );

    return `
      <details class="category" data-category="${escapeHtml(category)}" ${
        isOpen ? "open" : ""
      }>
        <summary>
          <span class="category-title">
            <span class="category-icon">
              <ha-icon icon="${escapeHtml(icon)}"></ha-icon>
            </span>
            <span>${escapeHtml(label)}</span>
          </span>
          ${this._categoryStatusSummary(statusCounts, language)}
          <span
            class="category-count"
            title="${escapeHtml(countLabel)}"
            aria-label="${escapeHtml(countLabel)}"
          >${measurements.length}</span>
          <ha-icon class="chevron" icon="mdi:chevron-down"></ha-icon>
        </summary>
        <div class="rows">
          ${measurements
            .map((measurement) =>
              this._measurementRow(measurement, language)
            )
            .join("")}
        </div>
      </details>
    `;
  }

  _measurementRow(measurement, language) {
    const t = TEXT[language];
    const status = measurement.status || {};
    const severity = status.severity || "unknown";
    const direction = status.direction;
    const current = measurementValue(measurement, language);
    const target = targetLabel(measurement, language);
    const previous = measurement.has_previous
      ? measurementValue(measurement, language, true)
      : "";
    const hasNumericDelta = typeof measurement.delta === "number";
    const delta = hasNumericDelta
      ? numericLabel(Math.abs(measurement.delta), language)
      : "";
    const deltaUnit = measurement.unit ? ` ${measurement.unit}` : "";
    const symbol = trendSymbol(measurement.trend);
    const progress = targetProgress(measurement);
    const progressTitle =
      progress === "improved"
        ? t.improved
        : progress === "worsened"
          ? t.worsened
          : progress === "same"
            ? t.unchanged
            : "";

    let comparison = "";
    if (this._config.show_previous !== false && measurement.has_previous) {
      comparison = `
        <span class="previous-value">
          ${escapeHtml(t.previous)}: ${escapeHtml(previous)}
        </span>
        ${
          hasNumericDelta
            ? `
              <span class="delta ${escapeHtml(progress)}" title="${escapeHtml(
                progressTitle
              )}">
                ${escapeHtml(symbol)} ${escapeHtml(delta)}${escapeHtml(
                  deltaUnit
                )}
              </span>
            `
            : ""
        }
      `;
    }

    const historyEnabled = Boolean(measurement.historical_statistic_id);

    return `
      <div
        class="measurement${historyEnabled ? " history-enabled" : ""}"
        data-category="${escapeHtml(measurement.category || "unknown")}"
        data-key="${escapeHtml(measurement.key || "unknown")}"
        ${historyEnabled ? 'role="button" tabindex="0"' : ""}
      >
        <div class="status-icon ${escapeHtml(severity)}">
          <span class="status-dot"></span>
          ${
            direction === "high"
              ? '<span class="direction">↑</span>'
              : direction === "low"
                ? '<span class="direction">↓</span>'
                : ""
          }
        </div>

        <div class="measurement-main">
          <div class="measurement-name">
            ${escapeHtml(measurement.name || measurement.key || "—")}
          </div>
          <div class="measurement-sub">
            ${
              target
                ? `<span class="target-value">${escapeHtml(
                    t.target
                  )}: ${escapeHtml(target)}</span>`
                : ""
            }
            ${comparison}
          </div>
        </div>

        <div class="measurement-value">
          <span>${escapeHtml(current)}</span>
          ${
            historyEnabled
              ? '<ha-icon class="history-indicator" icon="mdi:chart-line"></ha-icon>'
              : ""
          }
        </div>
      </div>
    `;
  }

  _styles() {
    return `
      :host {
        display: block;
      }

      ha-card {
        overflow: hidden;
        border-radius: var(--ha-card-border-radius, 18px);
        background:
          radial-gradient(
            circle at 0% 0%,
            color-mix(in srgb, var(--primary-color) 8%, transparent),
            transparent 34%
          ),
          var(--ha-card-background, var(--card-background-color));
      }

      .header {
        padding: 16px 16px 13px;
        border-bottom: 1px solid var(--divider-color);
      }

      .title-row {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr) auto;
        align-items: center;
        gap: 11px;
      }

      .brand-icon {
        display: grid;
        place-items: center;
        width: 42px;
        height: 42px;
        border-radius: 14px;
        background: color-mix(
          in srgb,
          var(--primary-color) 16%,
          transparent
        );
        color: var(--primary-color);
      }

      .brand-icon ha-icon {
        --mdc-icon-size: 25px;
      }

      .title-wrap {
        min-width: 0;
      }

      .title {
        color: var(--primary-text-color);
        font-size: 1.18rem;
        font-weight: 700;
        line-height: 1.2;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .meta {
        margin-top: 4px;
        color: var(--secondary-text-color);
        font-size: 0.82rem;
      }

      .overall {
        max-width: 132px;
        padding: 6px 9px;
        border-radius: 999px;
        font-size: 0.68rem;
        font-weight: 700;
        line-height: 1.15;
        text-align: center;
        color: var(--primary-text-color);
        background: var(--secondary-background-color);
      }

      .overall.ok {
        color: var(--success-color, #43a047);
        background: color-mix(
          in srgb,
          var(--success-color, #43a047) 13%,
          transparent
        );
      }

      .overall.warning {
        color: var(--warning-color, #f9a825);
        background: color-mix(
          in srgb,
          var(--warning-color, #f9a825) 13%,
          transparent
        );
      }

      .overall.critical {
        color: var(--error-color, #db4437);
        background: color-mix(
          in srgb,
          var(--error-color, #db4437) 13%,
          transparent
        );
      }

      .status-strip {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 7px;
        margin-top: 12px;
      }

      .status-count {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr) auto;
        align-items: center;
        gap: 5px;
        min-width: 0;
        padding: 6px 8px;
        border-radius: 11px;
        background: color-mix(
          in srgb,
          var(--secondary-background-color) 86%,
          transparent
        );
        color: var(--secondary-text-color);
        font-size: 0.71rem;
      }

      .status-count strong {
        color: var(--primary-text-color);
        font-size: 0.82rem;
      }

      .status-label {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .status-count .status-dot,
      .status-icon .status-dot {
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background: var(--disabled-text-color);
      }

      .ok .status-dot {
        background: var(--success-color, #43a047);
      }

      .warning .status-dot {
        background: var(--warning-color, #f9a825);
      }

      .critical .status-dot {
        background: var(--error-color, #db4437);
      }

      .previous-analysis {
        display: flex;
        align-items: center;
        gap: 5px;
        margin-top: 10px;
        color: var(--secondary-text-color);
        font-size: 0.75rem;
      }

      .previous-analysis strong {
        color: var(--primary-text-color);
        font-weight: 600;
      }

      .previous-analysis ha-icon {
        margin-right: 2px;
        --mdc-icon-size: 16px;
      }

      .previous-date {
        opacity: 0.85;
      }

      .info-panel {
        margin: 10px 8px 0;
        overflow: hidden;
        border: 1px solid color-mix(
          in srgb,
          var(--primary-color) 18%,
          var(--divider-color)
        );
        border-radius: 13px;
        background: color-mix(
          in srgb,
          var(--primary-color) 5%,
          var(--secondary-background-color)
        );
      }

      .info-panel > .info-summary {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr) auto;
        align-items: center;
        gap: 9px;
        padding: 12px 13px;
        list-style: none;
        cursor: pointer;
        color: var(--primary-text-color);
        font-size: 0.86rem;
        user-select: none;
      }

      .info-panel > .info-summary::-webkit-details-marker {
        display: none;
      }

      .info-panel > .info-summary:hover {
        background: color-mix(
          in srgb,
          var(--secondary-background-color) 55%,
          transparent
        );
      }

      .info-icon {
        display: grid;
        place-items: center;
        width: 28px;
        height: 28px;
        flex: 0 0 auto;
        border-radius: 9px;
        color: var(--primary-color);
        background: color-mix(
          in srgb,
          var(--primary-color) 12%,
          transparent
        );
      }

      .info-icon ha-icon {
        --mdc-icon-size: 18px;
      }

      .info-chevron {
        color: var(--secondary-text-color);
        transition: transform 160ms ease;
        --mdc-icon-size: 20px;
      }

      .info-panel[open] .info-chevron {
        transform: rotate(180deg);
      }

      .info-content {
        padding: 0 13px 13px;
      }

      .interpretation-text {
        color: var(--secondary-text-color);
        font-size: 0.82rem;
        line-height: 1.55;
        white-space: normal;
        overflow-wrap: anywhere;
      }

      .recommendation-system {
        margin-bottom: 10px;
        color: var(--secondary-text-color);
        font-size: 0.76rem;
        font-weight: 650;
      }


      .insight-comparison {
        margin-bottom: 10px;
        color: var(--secondary-text-color);
        font-size: 0.74rem;
        line-height: 1.4;
      }

      .insight-comparison strong {
        color: var(--primary-text-color);
      }

      .insight-list,
      .insight-trend-list {
        display: grid;
        gap: 8px;
      }

      .insight-item,
      .insight-trend-item {
        padding: 10px;
        border-radius: 11px;
        background: color-mix(
          in srgb,
          var(--secondary-background-color) 84%,
          transparent
        );
      }

      .insight-item-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
      }

      .insight-item-head strong {
        color: var(--primary-text-color);
        font-size: 0.82rem;
      }

      .insight-badge {
        padding: 2px 6px;
        border-radius: 999px;
        color: var(--secondary-text-color);
        background: color-mix(
          in srgb,
          var(--primary-color) 8%,
          transparent
        );
        font-size: 0.61rem;
        font-weight: 700;
        white-space: nowrap;
      }

      .insight-badge.new_issue,
      .insight-badge.worsened {
        color: var(--warning-color, var(--primary-text-color));
      }

      .insight-badge.resolved,
      .insight-badge.improved {
        color: var(--success-color, var(--primary-text-color));
      }

      .insight-values {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-top: 7px;
        color: var(--secondary-text-color);
        font-size: 0.73rem;
      }

      .insight-values ha-icon {
        --mdc-icon-size: 14px;
      }

      .insight-values strong {
        color: var(--primary-text-color);
      }

      .insight-trend-title {
        display: flex;
        align-items: center;
        gap: 6px;
        margin: 13px 0 8px;
        color: var(--primary-text-color);
        font-size: 0.78rem;
      }

      .insight-trend-title ha-icon {
        color: var(--primary-color);
        --mdc-icon-size: 16px;
      }

      .insight-trend-item {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr);
        align-items: center;
        gap: 9px;
      }

      .insight-trend-icon {
        display: grid;
        place-items: center;
        width: 30px;
        height: 30px;
        border-radius: 9px;
        color: var(--primary-color);
        background: color-mix(
          in srgb,
          var(--primary-color) 10%,
          transparent
        );
      }

      .insight-trend-icon ha-icon {
        --mdc-icon-size: 18px;
      }

      .insight-trend-item > div {
        display: grid;
        gap: 2px;
        min-width: 0;
      }

      .insight-trend-item strong {
        color: var(--primary-text-color);
        font-size: 0.78rem;
      }

      .insight-trend-item span,
      .insight-trend-item small,
      .insight-more {
        color: var(--secondary-text-color);
        font-size: 0.69rem;
        line-height: 1.35;
      }

      .insight-trend-item small {
        font-size: 0.65rem;
      }

      .insight-more {
        margin-top: 7px;
      }

      .insight-note {
        margin-top: 10px;
      }


      .profile-insight-list {
        display: grid;
        gap: 8px;
      }

      .profile-insight-item {
        padding: 10px;
        border-radius: 11px;
        background: color-mix(
          in srgb,
          var(--secondary-background-color) 84%,
          transparent
        );
      }

      .profile-insight-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 9px;
      }

      .profile-insight-head > div {
        display: grid;
        gap: 3px;
        min-width: 0;
      }

      .profile-insight-head strong {
        color: var(--primary-text-color);
        font-size: 0.82rem;
      }

      .profile-context-label {
        color: var(--secondary-text-color);
        font-size: 0.62rem;
        font-weight: 650;
      }

      .profile-attention {
        flex: 0 0 auto;
        padding: 2px 6px;
        border-radius: 999px;
        color: var(--secondary-text-color);
        background: color-mix(
          in srgb,
          var(--primary-color) 8%,
          transparent
        );
        font-size: 0.6rem;
        font-weight: 700;
        white-space: nowrap;
      }

      .profile-attention.high {
        color: var(--warning-color, var(--primary-text-color));
      }

      .profile-insight-value {
        margin-top: 7px;
        color: var(--primary-text-color);
        font-size: 0.78rem;
        font-weight: 700;
      }

      .profile-signal {
        display: flex;
        align-items: center;
        gap: 5px;
        margin-top: 6px;
        color: var(--secondary-text-color);
        font-size: 0.69rem;
      }

      .profile-signal ha-icon {
        color: var(--primary-color);
        --mdc-icon-size: 14px;
      }

      .profile-reason {
        margin-top: 7px;
        color: var(--secondary-text-color);
        font-size: 0.69rem;
        line-height: 1.45;
      }

      .profile-basis-note {
        margin-top: 10px;
      }

      .recommendation-list {
        display: grid;
        gap: 8px;
      }

      .recommendation-item {
        padding: 10px;
        border-radius: 11px;
        background: color-mix(
          in srgb,
          var(--secondary-background-color) 84%,
          transparent
        );
      }

      .recommendation-item-head {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 4px 10px;
      }

      .recommendation-item-head strong {
        color: var(--primary-text-color);
        font-size: 0.82rem;
      }

      .recommendation-item-head > div {
        display: grid;
        gap: 3px;
      }

      .recommendation-kind {
        width: fit-content;
        padding: 2px 6px;
        border-radius: 999px;
        color: var(--secondary-text-color);
        background: color-mix(
          in srgb,
          var(--primary-color) 9%,
          transparent
        );
        font-size: 0.61rem;
        font-weight: 650;
        letter-spacing: 0.02em;
      }

      .recommendation-values {
        color: var(--secondary-text-color);
        font-size: 0.72rem;
      }

      .recommendation-dose {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 10px;
        margin-top: 8px;
        color: var(--secondary-text-color);
        font-size: 0.76rem;
      }

      .recommendation-dose strong {
        color: var(--primary-color);
        font-size: 1rem;
      }

      .recommendation-product,
      .recommendation-action {
        margin-top: 5px;
        color: var(--secondary-text-color);
        font-size: 0.72rem;
        line-height: 1.4;
      }

      .laboratory-dose-row {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 10px;
        margin-top: 7px;
        color: var(--secondary-text-color);
        font-size: 0.76rem;
      }

      .laboratory-dose-row strong {
        color: var(--primary-color);
        font-size: 0.88rem;
      }

      .laboratory-report-volume {
        margin-top: 6px;
        color: var(--secondary-text-color);
        font-size: 0.69rem;
      }

      .laboratory-report-text {
        margin-top: 9px;
        padding: 10px;
        border-radius: 11px;
        color: var(--secondary-text-color);
        background: color-mix(
          in srgb,
          var(--secondary-background-color) 84%,
          transparent
        );
        font-size: 0.74rem;
        line-height: 1.5;
      }

      .laboratory-report-text strong {
        display: block;
        margin-bottom: 5px;
        color: var(--primary-text-color);
        font-size: 0.78rem;
      }

      .laboratory-source-note {
        margin-top: 10px;
      }

      .recommendation-schedule,
      .recommendation-warning {
        display: flex;
        align-items: flex-start;
        gap: 6px;
        margin-top: 7px;
        color: var(--secondary-text-color);
        font-size: 0.69rem;
        line-height: 1.4;
      }

      .recommendation-warning {
        color: var(--warning-color, var(--primary-text-color));
      }

      .recommendation-schedule ha-icon,
      .recommendation-warning ha-icon {
        flex: 0 0 auto;
        margin-top: 1px;
        --mdc-icon-size: 14px;
      }

      .recommendation-source {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        margin-top: 7px;
        color: var(--primary-color);
        font-size: 0.66rem;
        text-decoration: none;
      }

      .recommendation-source ha-icon {
        --mdc-icon-size: 13px;
      }

      .recommendation-empty {
        padding: 9px 10px;
        border-radius: 10px;
        color: var(--secondary-text-color);
        background: var(--secondary-background-color);
        font-size: 0.76rem;
        line-height: 1.45;
      }

      .recommendation-note {
        display: flex;
        align-items: flex-start;
        gap: 7px;
        margin-top: 9px;
        color: var(--secondary-text-color);
        font-size: 0.69rem;
        line-height: 1.45;
      }

      .recommendation-note ha-icon {
        flex: 0 0 auto;
        margin-top: 1px;
        color: var(--primary-color);
        --mdc-icon-size: 15px;
      }

      .aquarium-profile {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: 10px;
      }

      .profile-chip {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        min-height: 25px;
        padding: 3px 8px;
        border-radius: 999px;
        color: var(--secondary-text-color);
        background: color-mix(
          in srgb,
          var(--secondary-background-color) 88%,
          transparent
        );
        font-size: 0.7rem;
      }

      .profile-chip strong {
        color: var(--primary-text-color);
        font-weight: 650;
      }

      .profile-chip ha-icon {
        color: var(--primary-color);
        --mdc-icon-size: 15px;
      }

      .categories {
        padding: 8px;
      }

      details.category {
        border-radius: 13px;
        overflow: hidden;
      }

      details.category + details.category {
        margin-top: 4px;
      }

      details.category > summary {
        list-style: none;
        cursor: pointer;
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto auto auto;
        align-items: center;
        gap: 8px;
        padding: 10px 9px;
        border-radius: 11px;
        color: var(--primary-text-color);
        user-select: none;
      }

      details.category > summary::-webkit-details-marker {
        display: none;
      }

      details.category > summary:hover {
        background: var(--secondary-background-color);
      }

      .category-title {
        display: flex;
        align-items: center;
        min-width: 0;
        gap: 8px;
        font-size: 0.9rem;
        font-weight: 700;
      }

      .category-icon {
        display: grid;
        place-items: center;
        width: 28px;
        height: 28px;
        border-radius: 9px;
        color: var(--primary-color);
        background: color-mix(
          in srgb,
          var(--primary-color) 9%,
          transparent
        );
      }

      .category-icon ha-icon {
        --mdc-icon-size: 18px;
      }

      .category-status {
        display: inline-flex;
        align-items: center;
        justify-content: flex-end;
        gap: 7px;
        min-width: 0;
      }

      .category-status-item {
        display: inline-flex;
        align-items: center;
        gap: 3px;
        color: var(--secondary-text-color);
        font-size: 0.64rem;
        font-weight: 700;
        line-height: 1;
        white-space: nowrap;
      }

      .category-status-item .status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--disabled-text-color);
      }

      .category-status-item.ok .status-dot {
        background: var(--success-color, #43a047);
      }

      .category-status-item.warning .status-dot {
        background: var(--warning-color, #f9a825);
      }

      .category-status-item.critical .status-dot {
        background: var(--error-color, #db4437);
      }

      .category-status-item.unknown .status-dot {
        background: var(--disabled-text-color);
      }

      .category-status-count {
        min-width: 0.65rem;
        text-align: left;
      }

      .category-count {
        min-width: 25px;
        padding: 3px 7px;
        border-radius: 999px;
        text-align: center;
        color: var(--secondary-text-color);
        background: var(--secondary-background-color);
        font-size: 0.7rem;
      }

      .chevron {
        color: var(--secondary-text-color);
        transition: transform 160ms ease;
        --mdc-icon-size: 20px;
      }

      details[open] .chevron {
        transform: rotate(180deg);
      }

      .rows {
        padding: 0 4px 5px;
      }

      .measurement {
        display: grid;
        grid-template-columns: 30px minmax(0, 1fr) auto;
        align-items: center;
        gap: 9px;
        min-height: 56px;
        padding: 7px 8px;
        border-top: 1px solid var(--divider-color);
      }

      .measurement.history-enabled {
        cursor: pointer;
        border-radius: 10px;
        transition: background 120ms ease;
      }

      .measurement.history-enabled:hover {
        background: color-mix(
          in srgb,
          var(--secondary-background-color) 65%,
          transparent
        );
      }

      .measurement.history-enabled:focus-visible {
        outline: 2px solid var(--primary-color);
        outline-offset: -2px;
      }

      .status-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 2px;
        width: 28px;
        height: 28px;
        border-radius: 9px;
        color: var(--secondary-text-color);
        background: var(--secondary-background-color);
      }

      .status-icon .status-dot {
        width: 9px;
        height: 9px;
      }

      .direction {
        font-size: 0.78rem;
        font-weight: 800;
        line-height: 1;
      }

      .status-icon.ok {
        color: var(--success-color, #43a047);
      }

      .status-icon.warning {
        color: var(--warning-color, #f9a825);
      }

      .status-icon.critical {
        color: var(--error-color, #db4437);
      }

      .measurement-main {
        min-width: 0;
      }

      .measurement-name {
        color: var(--primary-text-color);
        font-size: 0.9rem;
        font-weight: 650;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .measurement-sub {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 4px 8px;
        margin-top: 4px;
        color: var(--secondary-text-color);
        font-size: 0.69rem;
      }

      .target-value,
      .previous-value {
        white-space: nowrap;
      }

      .delta {
        display: inline-flex;
        align-items: center;
        min-height: 18px;
        padding: 1px 5px;
        border-radius: 999px;
        font-weight: 700;
        white-space: nowrap;
        background: var(--secondary-background-color);
      }

      .delta.improved {
        color: var(--success-color, #43a047);
        background: color-mix(
          in srgb,
          var(--success-color, #43a047) 10%,
          transparent
        );
      }

      .delta.worsened {
        color: var(--error-color, #db4437);
        background: color-mix(
          in srgb,
          var(--error-color, #db4437) 10%,
          transparent
        );
      }

      .delta.same,
      .delta.neutral {
        color: var(--secondary-text-color);
      }

      .measurement-value {
        display: inline-flex;
        max-width: 150px;
        align-items: center;
        justify-content: flex-end;
        gap: 5px;
        color: var(--primary-text-color);
        font-size: 0.91rem;
        font-weight: 750;
        text-align: right;
        overflow-wrap: anywhere;
      }

      .history-indicator {
        flex: 0 0 auto;
        color: var(--secondary-text-color);
        opacity: 0.7;
        --mdc-icon-size: 15px;
      }

      .history-dialog {
        width: min(92vw, 720px);
        max-width: 720px;
        max-height: min(88vh, 760px);
        margin: auto;
        padding: 0;
        overflow: visible;
        border: 1px solid var(--divider-color);
        border-radius: 20px;
        background:
          radial-gradient(
            circle at 0% 0%,
            color-mix(in srgb, var(--primary-color) 8%, transparent),
            transparent 36%
          ),
          var(--ha-card-background, var(--card-background-color));
        color: var(--primary-text-color);
        box-shadow: 0 18px 60px rgba(0, 0, 0, 0.42);
      }

      .history-dialog::backdrop {
        background: rgba(0, 0, 0, 0.66);
        backdrop-filter: blur(4px);
      }

      .history-dialog-inner {
        position: relative;
        max-height: min(88vh, 760px);
        padding: 18px;
        overflow-y: auto;
        box-sizing: border-box;
      }

      .history-close {
        position: absolute;
        z-index: 2;
        top: 12px;
        right: 12px;
        display: grid;
        width: 38px;
        height: 38px;
        place-items: center;
        padding: 0;
        border: 0;
        border-radius: 12px;
        color: var(--secondary-text-color);
        background: var(--secondary-background-color);
        cursor: pointer;
      }

      .history-close:hover {
        color: var(--primary-text-color);
      }

      .history-close ha-icon {
        --mdc-icon-size: 21px;
      }

      .message {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 22px;
      }

      .message > ha-icon {
        color: var(--primary-color);
        --mdc-icon-size: 30px;
      }

      .message-title {
        color: var(--primary-text-color);
        font-weight: 650;
      }

      .message-text {
        margin-top: 4px;
        color: var(--secondary-text-color);
        font-size: 0.85rem;
      }

      @media (max-width: 520px) {
        .header {
          padding: 14px 13px 12px;
        }

        .title-row {
          gap: 9px;
        }

        .brand-icon {
          width: 39px;
          height: 39px;
          border-radius: 13px;
        }

        .title {
          font-size: 1.08rem;
        }

        .meta {
          font-size: 0.77rem;
        }

        .overall {
          max-width: 105px;
          padding: 5px 7px;
          font-size: 0.62rem;
        }

        .status-strip {
          gap: 5px;
          margin-top: 10px;
        }

        .status-count {
          grid-template-columns: auto minmax(0, 1fr) auto;
          gap: 4px;
          padding: 5px 6px;
          font-size: 0.64rem;
        }

        .status-count strong {
          font-size: 0.75rem;
        }

        .categories {
          padding: 6px;
        }

        summary {
          gap: 6px;
          padding: 9px 7px;
        }

        .category-status {
          gap: 5px;
        }

        .category-status-item {
          gap: 2px;
          font-size: 0.6rem;
        }

        .category-status-item .status-dot {
          width: 6px;
          height: 6px;
        }

        .measurement {
          grid-template-columns: 28px minmax(0, 1fr) minmax(74px, auto);
          gap: 7px;
          padding-inline: 6px;
        }

        .measurement-value {
          max-width: 126px;
          font-size: 0.85rem;
        }

        .history-dialog {
          width: min(94vw, 720px);
          border-radius: 17px;
        }

        .history-dialog-inner {
          padding: 15px;
        }

        .measurement-sub {
          gap: 3px 6px;
          font-size: 0.65rem;
        }
      }

      @media (max-width: 370px) {
        .status-label {
          display: none;
        }

        .status-count {
          grid-template-columns: auto auto;
          justify-content: center;
        }

        .overall {
          max-width: 92px;
        }
      }
    `;
  }
}

if (!customElements.get(CARD_TAG)) {
  customElements.define(CARD_TAG, ReefIcpCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === CARD_TAG)) {
  window.customCards.push({
    type: CARD_TAG,
    name: "Reef ICP Card",
    description:
      "Displays multi-provider reef ICP analyses with targets, status, comparison and interactive measurement history.",
    preview: true,
    getEntitySuggestion: (hass, entityId) => {
      const state = hass?.states?.[entityId];
      const attrs = state?.attributes || {};
      if (
        !entityId?.startsWith("sensor.") ||
        !Array.isArray(attrs.measurements) ||
        !("analysis_number" in attrs) ||
        !("status_counts" in attrs)
      ) {
        return null;
      }

      return {
        config: {
          type: "custom:reef-icp-card",
          entity: entityId,
          show_previous: true,
        },
      };
    },
  });
}

console.info(
  `%c REEF ICP CARD %c v${CARD_VERSION} `,
  "background:#1686a8;color:white;font-weight:700;padding:2px 6px;border-radius:4px 0 0 4px;",
  "background:#1f2937;color:white;padding:2px 6px;border-radius:0 4px 4px 0;"
);
