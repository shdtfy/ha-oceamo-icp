const REEF_ICP_V015_EXTENSION = "0.15.0";

const METHOD_TEXT = {
  de: {
    title: "Riff-/Nährstoffmethode",
    source: "Herstellerquelle öffnen",
    amount: "Menge",
    range: "Bereich",
    frequency: "Rhythmus",
    flow: "Durchfluss",
    change: "Wechsel",
    weeks: "Wochen",
    days: "Tage",
    daily: "täglich",
    every2Days: "alle 2 Tage",
    every4Days: "alle 4 Tage",
    continuous: "dauerhaft",
    every6Weeks: "alle 6 Wochen",
    stage: "Phase",
    maintenance: "Dauerbetrieb",
    establishment: "Einführungsphase",
    week: "Woche",
    dose: "Dosis",
    note: "Hinweis",
    methodInfo: "Herstellerbasierte Vorgaben für die ausgewählte Riff-/Nährstoffmethode. Sie sind getrennt vom Versorgungssystem.",
    reactorFlow: "Reaktor-Durchfluss",
    mediaChange: "Medienwechsel",
    mediaFraction: "Anteil wechseln",
    startAmount: "Startmenge",
    maximumAmount: "Maximalmenge",
    cleanEvery: "Reinigen",
    replaceEvery: "Ersetzen",
    microbacter: "MicroBacter7",
    biofuel: "Reef BioFuel",
    perDay: "/Tag",
    perWeek: "/Woche",
    noGuidance: "Für diese Methode sind aktuell keine berechenbaren Vorgaben hinterlegt.",
  },
  en: {
    title: "Reef / nutrient method",
    source: "Open manufacturer source",
    amount: "Amount",
    range: "Range",
    frequency: "Frequency",
    flow: "Flow",
    change: "Change",
    weeks: "weeks",
    days: "days",
    daily: "daily",
    every2Days: "every 2 days",
    every4Days: "every 4 days",
    continuous: "continuous",
    every6Weeks: "every 6 weeks",
    stage: "Stage",
    maintenance: "Maintenance",
    establishment: "Establishment phase",
    week: "Week",
    dose: "Dose",
    note: "Note",
    methodInfo: "Manufacturer-based guidance for the selected reef / nutrient method. It is independent of the mineral supply system.",
    reactorFlow: "Reactor flow",
    mediaChange: "Media change",
    mediaFraction: "Replace fraction",
    startAmount: "Starting amount",
    maximumAmount: "Maximum amount",
    cleanEvery: "Clean",
    replaceEvery: "Replace",
    microbacter: "MicroBacter7",
    biofuel: "Reef BioFuel",
    perDay: "/day",
    perWeek: "/week",
    noGuidance: "No calculated guidance is stored for this method yet.",
  },
};

function extLanguage(hass) {
  return String(hass?.language || hass?.locale?.language || "en")
    .toLowerCase()
    .startsWith("de")
    ? "de"
    : "en";
}

function extEscape(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function extNumber(value, language, digits = 3) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "";
  return new Intl.NumberFormat(language === "de" ? "de-DE" : "en-US", {
    maximumFractionDigits: digits,
  }).format(number);
}

function extFrequency(value, t) {
  const map = {
    daily: t.daily,
    daily_single_bolus: t.daily,
    every_2_days: t.every2Days,
    every_4_days: t.every4Days,
    continuous: t.continuous,
  };
  return map[value] || String(value || "").replaceAll("_", " ");
}

function extLine(icon, label, value) {
  if (value === undefined || value === null || value === "") return "";
  return `
    <div class="reef-method-line">
      <ha-icon icon="${extEscape(icon)}"></ha-icon>
      <span>${extEscape(label)}</span>
      <strong>${extEscape(value)}</strong>
    </div>
  `;
}

function extItem(item, language, t) {
  if (!item || typeof item !== "object") return "";
  const unit = item.unit || "";
  const name = item.product || item.stage || item.key || "—";
  const lines = [];

  if (item.stage) lines.push(extLine("mdi:timeline-clock-outline", t.stage, item.stage));

  if (Number.isFinite(Number(item.amount))) {
    lines.push(
      extLine(
        "mdi:beaker-outline",
        t.amount,
        `${extNumber(item.amount, language)}${unit ? ` ${unit}` : ""}`
      )
    );
  }
  if (Number.isFinite(Number(item.minimum)) || Number.isFinite(Number(item.maximum))) {
    const min = Number.isFinite(Number(item.minimum)) ? extNumber(item.minimum, language) : "—";
    const max = Number.isFinite(Number(item.maximum)) ? extNumber(item.maximum, language) : "—";
    lines.push(extLine("mdi:arrow-expand-horizontal", t.range, `${min}–${max}${unit ? ` ${unit}` : ""}`));
  }
  if (item.frequency) {
    lines.push(extLine("mdi:calendar-sync-outline", t.frequency, extFrequency(item.frequency, t)));
  }
  if (item.clean_every_days) {
    lines.push(extLine("mdi:broom", t.cleanEvery, `${item.clean_every_days} ${t.days}`));
  }
  if (item.replace_every_weeks) {
    lines.push(extLine("mdi:refresh", t.replaceEvery, `${item.replace_every_weeks} ${t.weeks}`));
  }
  if (Number.isFinite(Number(item.max_reactor_flow_l_h))) {
    lines.push(extLine("mdi:pump", t.reactorFlow, `≤ ${extNumber(item.max_reactor_flow_l_h, language)} L/h`));
  }
  if (Number.isFinite(Number(item.start_amount))) {
    lines.push(extLine("mdi:play-outline", t.startAmount, `${extNumber(item.start_amount, language)}${unit ? ` ${unit}` : ""}`));
  }
  if (Number.isFinite(Number(item.maximum_amount))) {
    lines.push(extLine("mdi:gauge-full", t.maximumAmount, `${extNumber(item.maximum_amount, language)}${unit ? ` ${unit}` : ""}`));
  }
  if (Number.isFinite(Number(item.neozeo_add_g_per_week))) {
    lines.push(extLine("mdi:grain", "NeoZeo", `${extNumber(item.neozeo_add_g_per_week, language)} g ${t.perWeek}`));
  }
  if (Number.isFinite(Number(item.reactor_flow_l_h))) {
    lines.push(extLine("mdi:pump", t.reactorFlow, `${extNumber(item.reactor_flow_l_h, language)} L/h`));
  }
  if (Number.isFinite(Number(item.microbacter7_ml_daily))) {
    lines.push(extLine("mdi:bacteria-outline", t.microbacter, `${extNumber(item.microbacter7_ml_daily, language)} ml ${t.perDay}`));
  }
  if (Number.isFinite(Number(item.reef_biofuel_ml_daily))) {
    lines.push(extLine("mdi:flask-outline", t.biofuel, `${extNumber(item.reef_biofuel_ml_daily, language)} ml ${t.perDay}`));
  }
  if (Number.isFinite(Number(item.media_change_fraction))) {
    lines.push(extLine("mdi:refresh", t.mediaFraction, `${extNumber(item.media_change_fraction * 100, language, 1)} %`));
  }
  if (Number.isFinite(Number(item.media_change_every_weeks))) {
    lines.push(extLine("mdi:calendar-refresh", t.mediaChange, `${extNumber(item.media_change_every_weeks, language)} ${t.weeks}`));
  }
  if (item.note) {
    lines.push(extLine("mdi:information-outline", t.note, item.note));
  }

  return `
    <div class="reef-method-item">
      <div class="reef-method-item-title">${extEscape(name)}</div>
      ${lines.join("")}
    </div>
  `;
}

function extEstablishment(guidance, language, t) {
  const steps = Array.isArray(guidance?.establishment) ? guidance.establishment : [];
  if (!steps.length) return "";
  return `
    <div class="reef-method-establishment">
      <div class="reef-method-subtitle">
        <ha-icon icon="mdi:stairs-up"></ha-icon>
        <strong>${extEscape(t.establishment)}</strong>
      </div>
      <div class="reef-method-ramp">
        ${steps
          .map(
            (step) => `
              <span>
                ${extEscape(t.week)} ${extEscape(step.week)}
                <strong>${extEscape(extNumber(step.dose_ml, language))} ml</strong>
              </span>
            `
          )
          .join("")}
      </div>
    </div>
  `;
}

function extSupplyMaintenance(card, attrs, language, t) {
  const supply = attrs.supply_recommendations;
  const guidance = supply?.maintenance_guidance;
  if (!guidance || typeof guidance !== "object") return;

  const shadow = card.shadowRoot;
  const content = shadow?.querySelector("details.recommendation-panel .recommendation-content");
  if (!content || content.querySelector(".supply-maintenance-v015")) return;

  const labels = language === "de"
    ? {
        start_daily_ml: "Startdosis täglich",
        weekly_increase_ml: "Wöchentliche Erhöhung",
        max_daily_ml: "Maximal täglich",
        typical_daily_ml_each: "Typisch täglich je Komponente",
        weekly_ml_each: "Wöchentlich je Komponente",
        equal_amounts: "Gleiche Mengen",
        split_into_small_doses: "Auf kleine Dosen verteilen",
        variant: "Variante",
        regulator: "Regelgröße",
      }
    : {
        start_daily_ml: "Starting daily dose",
        weekly_increase_ml: "Weekly increase",
        max_daily_ml: "Maximum daily dose",
        typical_daily_ml_each: "Typical daily dose per component",
        weekly_ml_each: "Weekly dose per component",
        equal_amounts: "Equal amounts",
        split_into_small_doses: "Split into small doses",
        variant: "Variant",
        regulator: "Regulator",
      };

  const mlKeys = new Set([
    "start_daily_ml",
    "weekly_increase_ml",
    "max_daily_ml",
    "typical_daily_ml_each",
    "weekly_ml_each",
  ]);

  const valueText = (key, value) => {
    if (typeof value === "boolean") {
      return value ? (language === "de" ? "Ja" : "Yes") : (language === "de" ? "Nein" : "No");
    }
    if (mlKeys.has(key) && Number.isFinite(Number(value))) {
      return `${extNumber(value, language)} ml`;
    }
    if (Array.isArray(value)) return value.join(" · ");
    return String(value ?? "");
  };

  const rows = [];
  for (const key of Object.keys(labels)) {
    if (!(key in guidance)) continue;
    rows.push(extLine("mdi:tune-variant", labels[key], valueText(key, guidance[key])));
  }

  if (Array.isArray(guidance.products)) {
    rows.unshift(extLine("mdi:flask-multiple-outline", language === "de" ? "Produkte" : "Products", guidance.products.join(" · ")));
  } else if (guidance.product) {
    rows.unshift(extLine("mdi:flask-outline", language === "de" ? "Produkt" : "Product", guidance.product));
  }

  if (guidance.note) {
    rows.push(extLine("mdi:information-outline", t.note, guidance.note));
  }

  if (!rows.length) return;
  const box = document.createElement("div");
  box.className = "reef-method-item supply-maintenance-v015";
  box.innerHTML = `
    <div class="reef-method-item-title">
      ${extEscape(language === "de" ? "Laufende Systemdosierung" : "Ongoing system dosing")}
    </div>
    ${rows.join("")}
  `;

  const correctionNote = content.querySelector(".recommendation-note:last-of-type");
  if (correctionNote) correctionNote.insertAdjacentElement("beforebegin", box);
  else content.appendChild(box);
}

function extInject(card) {
  const shadow = card.shadowRoot;
  if (!shadow) return;
  const state = card._config?.entity ? card._hass?.states?.[card._config.entity] : null;
  const attrs = state?.attributes || {};
  const language = extLanguage(card._hass);
  const t = METHOD_TEXT[language];
  extSupplyMaintenance(card, attrs, language, t);

  const method = attrs.reef_method;
  const guidance = attrs.reef_method_guidance;
  if (!method || method === "none" || !guidance || typeof guidance !== "object") return;
  const methodName = attrs.reef_method_name || guidance.method_name || method;

  const profile = shadow.querySelector(".aquarium-profile");
  if (profile && !profile.querySelector(".reef-method-chip")) {
    profile.insertAdjacentHTML(
      "beforeend",
      `
        <span class="profile-chip reef-method-chip">
          <ha-icon icon="mdi:filter-variant"></ha-icon>
          ${extEscape(methodName)}
        </span>
      `
    );
  }

  if (shadow.querySelector(".reef-method-panel")) return;

  const categories = shadow.querySelector(".categories");
  if (!categories) return;

  const items = Array.isArray(guidance.items) ? guidance.items : [];
  const sourceUrl = String(guidance.source_url || "").startsWith("https://")
    ? guidance.source_url
    : "";
  const secondaryUrl = String(guidance.secondary_source_url || "").startsWith("https://")
    ? guidance.secondary_source_url
    : "";

  const panel = document.createElement("details");
  panel.className = "info-panel reef-method-panel";
  panel.innerHTML = `
    <summary class="info-summary">
      <span class="info-icon"><ha-icon icon="mdi:filter-variant"></ha-icon></span>
      <strong>${extEscape(t.title)}</strong>
      <ha-icon class="info-chevron" icon="mdi:chevron-down"></ha-icon>
    </summary>
    <div class="info-content reef-method-content">
      <div class="recommendation-system">${extEscape(methodName)}</div>
      <div class="reef-method-intro">${extEscape(t.methodInfo)}</div>
      ${extEstablishment(guidance, language, t)}
      <div class="reef-method-grid">
        ${items.length ? items.map((item) => extItem(item, language, t)).join("") : `<div class="recommendation-empty">${extEscape(t.noGuidance)}</div>`}
      </div>
      ${guidance.note ? `<div class="recommendation-note"><ha-icon icon="mdi:information-outline"></ha-icon><span>${extEscape(guidance.note)}</span></div>` : ""}
      ${guidance.caution ? `<div class="recommendation-note reef-method-caution"><ha-icon icon="mdi:alert-outline"></ha-icon><span>${extEscape(guidance.caution)}</span></div>` : ""}
      ${sourceUrl ? `<a class="reef-method-source" href="${extEscape(sourceUrl)}" target="_blank" rel="noopener noreferrer"><ha-icon icon="mdi:open-in-new"></ha-icon>${extEscape(t.source)}</a>` : ""}
      ${secondaryUrl ? `<a class="reef-method-source" href="${extEscape(secondaryUrl)}" target="_blank" rel="noopener noreferrer"><ha-icon icon="mdi:open-in-new"></ha-icon>${extEscape(t.source)} 2</a>` : ""}
    </div>
  `;

  categories.insertAdjacentElement("afterend", panel);

  const style = document.createElement("style");
  style.dataset.reefIcpV015 = "true";
  style.textContent = `
    .reef-method-content { display: grid; gap: 12px; }
    .reef-method-intro { color: var(--secondary-text-color); font-size: 0.92rem; line-height: 1.45; }
    .reef-method-grid { display: grid; gap: 10px; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); }
    .reef-method-item { border: 1px solid var(--divider-color); border-radius: 14px; padding: 12px; background: color-mix(in srgb, var(--card-background-color) 92%, var(--primary-color) 8%); }
    .reef-method-item-title { font-weight: 700; margin-bottom: 8px; }
    .reef-method-line { display: grid; grid-template-columns: 20px minmax(70px, 1fr) auto; gap: 7px; align-items: center; padding: 4px 0; font-size: 0.88rem; }
    .reef-method-line ha-icon { --mdc-icon-size: 18px; color: var(--secondary-text-color); }
    .reef-method-line span { color: var(--secondary-text-color); }
    .reef-method-line strong { text-align: right; font-weight: 650; }
    .reef-method-subtitle { display: flex; align-items: center; gap: 7px; margin-bottom: 8px; }
    .reef-method-ramp { display: flex; gap: 6px; flex-wrap: wrap; }
    .reef-method-ramp span { display: inline-flex; gap: 5px; align-items: center; border: 1px solid var(--divider-color); border-radius: 999px; padding: 5px 9px; font-size: 0.82rem; }
    .reef-method-source { display: inline-flex; align-items: center; gap: 6px; color: var(--primary-color); text-decoration: none; font-weight: 600; width: fit-content; }
    .reef-method-source ha-icon { --mdc-icon-size: 18px; }
    .reef-method-caution { border-color: var(--warning-color, #ff9800); }
  `;
  shadow.appendChild(style);
}

customElements.whenDefined("reef-icp-card").then(() => {
  const Card = customElements.get("reef-icp-card");
  if (!Card || Card.prototype.__reefIcpV015Patched) return;
  const originalRender = Card.prototype._render;
  if (typeof originalRender !== "function") return;

  Card.prototype._render = function (...args) {
    const result = originalRender.apply(this, args);
    try {
      extInject(this);
    } catch (error) {
      console.warn("Reef ICP 0.15 card extension failed", error);
    }
    return result;
  };
  Card.prototype.__reefIcpV015Patched = true;

  document.querySelectorAll("reef-icp-card").forEach((card) => {
    try {
      card._render?.();
    } catch (_error) {
      // The normal Home Assistant lifecycle will render it on the next state update.
    }
  });
});

console.info(`%c REEF-ICP-CARD-EXT ${REEF_ICP_V015_EXTENSION} `, "background:#00695c;color:white;font-weight:700;");
