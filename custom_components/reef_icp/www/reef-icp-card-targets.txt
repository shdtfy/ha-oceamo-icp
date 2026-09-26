const REEF_ICP_TARGET_PATCH_VERSION = "0.13.5";

function reefIcpPatchLanguage(host) {
  const value =
    host?._hass?.locale?.language ||
    host?._hass?.language ||
    document.documentElement.lang ||
    navigator.language ||
    "en";
  return String(value).toLowerCase().startsWith("de") ? "de" : "en";
}

function reefIcpPatchText(language) {
  return language === "de"
    ? {
        personalTarget: "Dein Ziel",
        laboratoryTarget: "Labor",
        belowPersonal: "unter deinem Ziel",
        abovePersonal: "über deinem Ziel",
        customTargets: "Eigene Zielwerte",
        notDetectable: "Nicht nachweisbar",
        notDetermined: "Nicht bestimmt",
        unclear: "Sonst unklar",
      }
    : {
        personalTarget: "Your target",
        laboratoryTarget: "Lab",
        belowPersonal: "below your target",
        abovePersonal: "above your target",
        customTargets: "Personal targets",
        notDetectable: "Not detectable",
        notDetermined: "Not determined",
        unclear: "Other unclear",
      };
}

function reefIcpPatchNumber(value, language) {
  if (typeof value !== "number" || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat(language === "de" ? "de-DE" : "en-US", {
    maximumFractionDigits: 6,
  }).format(value);
}

function reefIcpPatchTarget(target, unit, language) {
  if (!target || typeof target !== "object") return "";

  let value = "";
  if (target.type === "range") {
    if (typeof target.min !== "number" || typeof target.max !== "number") {
      return "";
    }
    value = `${reefIcpPatchNumber(target.min, language)}–${reefIcpPatchNumber(
      target.max,
      language
    )}`;
  } else if (target.type === "exact") {
    if (typeof target.value !== "number") return "";
    value = reefIcpPatchNumber(target.value, language);
  } else if (target.type === "upper_limit") {
    if (typeof target.max !== "number") return "";
    value = `< ${reefIcpPatchNumber(target.max, language)}`;
  } else if (target.type === "lower_limit") {
    if (typeof target.min !== "number") return "";
    value = `> ${reefIcpPatchNumber(target.min, language)}`;
  } else {
    return "";
  }

  return unit ? `${value} ${unit}` : value;
}

function reefIcpUnknownKind(measurement) {
  const severity = measurement?.status?.severity || "unknown";
  if (severity !== "unknown") return null;

  const raw = String(measurement?.raw_value ?? "")
    .trim()
    .toLowerCase();

  if (raw === "n.n.") return "not_detectable";
  if (
    raw === "n.g." ||
    raw === "n.b." ||
    raw === "---" ||
    measurement?.determined === false
  ) {
    return "not_determined";
  }
  return "unclear";
}

function reefIcpUnknownBreakdown(measurements) {
  const counts = {
    not_detectable: 0,
    not_determined: 0,
    unclear: 0,
  };
  for (const measurement of measurements || []) {
    const kind = reefIcpUnknownKind(measurement);
    if (kind) counts[kind] += 1;
  }
  return counts;
}

function reefIcpCreateStatusPill(documentRef, label, count) {
  const pill = documentRef.createElement("div");
  pill.className = "status-count unknown reef-icp-split-unknown";

  const dot = documentRef.createElement("span");
  dot.className = "status-dot";

  const text = documentRef.createElement("span");
  text.className = "status-label";
  text.textContent = label;

  const strong = documentRef.createElement("strong");
  strong.textContent = String(count);

  pill.append(dot, text, strong);
  return pill;
}

function reefIcpDecorateUnknownCounts(card, measurements, language) {
  const root = card.shadowRoot;
  if (!root) return;

  const unknownPill = root.querySelector(
    ".status-strip > .status-count.unknown:not(.reef-icp-split-unknown)"
  );
  if (!unknownPill) return;

  const t = reefIcpPatchText(language);
  const counts = reefIcpUnknownBreakdown(measurements);
  const replacements = [
    [t.notDetectable, counts.not_detectable],
    [t.notDetermined, counts.not_determined],
    [t.unclear, counts.unclear],
  ].filter(([, count]) => count > 0);

  for (const [label, count] of replacements) {
    unknownPill.parentNode?.insertBefore(
      reefIcpCreateStatusPill(root.ownerDocument, label, count),
      unknownPill
    );
  }
  unknownPill.remove();

  for (const details of root.querySelectorAll("details.category")) {
    const category = details.dataset.category || "unknown";
    const categoryMeasurements = (measurements || []).filter(
      (measurement) => (measurement?.category || "unknown") === category
    );
    const categoryCounts = reefIcpUnknownBreakdown(categoryMeasurements);
    const unknownItem = details.querySelector(
      ".category-status-item.unknown:not(.reef-icp-split-unknown)"
    );
    if (!unknownItem) continue;

    const parent = unknownItem.parentNode;
    const miniItems = [
      [t.notDetectable, categoryCounts.not_detectable],
      [t.notDetermined, categoryCounts.not_determined],
      [t.unclear, categoryCounts.unclear],
    ].filter(([, count]) => count > 0);

    for (const [label, count] of miniItems) {
      const item = root.ownerDocument.createElement("span");
      item.className =
        "category-status-item unknown reef-icp-split-unknown";
      item.title = `${label}: ${count}`;

      const dot = root.ownerDocument.createElement("span");
      dot.className = "status-dot";

      const countEl = root.ownerDocument.createElement("span");
      countEl.className = "category-status-count";
      countEl.textContent = String(count);

      item.append(dot, countEl);
      parent?.insertBefore(item, unknownItem);
    }
    unknownItem.remove();
  }
}

function reefIcpPersonalRelation(measurement) {
  const target = measurement?.custom_target;
  const current = measurement?.value;

  if (
    !target ||
    target.type !== "range" ||
    typeof target.min !== "number" ||
    typeof target.max !== "number" ||
    typeof current !== "number" ||
    Number.isNaN(current)
  ) {
    return null;
  }

  if (current < target.min) return "low";
  if (current > target.max) return "high";
  return "ok";
}

function reefIcpDecoratePersonalTargets(card, measurements, language) {
  const root = card.shadowRoot;
  if (!root) return;
  const t = reefIcpPatchText(language);

  let configured = 0;

  for (const measurement of measurements || []) {
    const customTarget = measurement?.custom_target;
    if (!customTarget || customTarget.type !== "range") continue;
    configured += 1;

    const category = String(measurement.category || "unknown");
    const key = String(measurement.key || "unknown");
    const rows = [...root.querySelectorAll(".measurement")];
    const row = rows.find(
      (candidate) =>
        candidate.dataset.category === category && candidate.dataset.key === key
    );
    if (!row) continue;

    const sub = row.querySelector(".measurement-sub");
    if (!sub) continue;

    const personalLabel = reefIcpPatchTarget(
      customTarget,
      measurement.unit,
      language
    );
    const laboratoryLabel = reefIcpPatchTarget(
      measurement.laboratory_target || measurement.target,
      measurement.unit,
      language
    );

    let targetSpan = sub.querySelector(".target-value");
    if (!targetSpan) {
      targetSpan = root.ownerDocument.createElement("span");
      targetSpan.className = "target-value";
      sub.prepend(targetSpan);
    }
    targetSpan.textContent = `${t.personalTarget}: ${personalLabel}`;

    if (
      laboratoryLabel &&
      !sub.querySelector(".reef-icp-laboratory-target")
    ) {
      const labSpan = root.ownerDocument.createElement("span");
      labSpan.className =
        "target-value reef-icp-laboratory-target";
      labSpan.textContent = `${t.laboratoryTarget}: ${laboratoryLabel}`;
      targetSpan.insertAdjacentElement("afterend", labSpan);
    }

    const relation = reefIcpPersonalRelation(measurement);
    if (
      (relation === "low" || relation === "high") &&
      !sub.querySelector(".reef-icp-personal-state")
    ) {
      const state = root.ownerDocument.createElement("span");
      state.className = `reef-icp-personal-state ${relation}`;
      state.textContent =
        relation === "low"
          ? `↓ ${t.belowPersonal}`
          : `↑ ${t.abovePersonal}`;
      sub.append(state);
    }
  }

  if (configured > 0) {
    let profile = root.querySelector(".aquarium-profile");
    if (profile && !profile.querySelector(".reef-icp-custom-target-chip")) {
      const chip = root.ownerDocument.createElement("span");
      chip.className = "profile-chip reef-icp-custom-target-chip";
      chip.innerHTML =
        '<ha-icon icon="mdi:target-account"></ha-icon>' +
        `<strong>${t.customTargets}:</strong> ${configured}`;
      profile.append(chip);
    }
  }
}

function reefIcpInstallPatchStyles(card) {
  const root = card.shadowRoot;
  if (!root || root.querySelector("style[data-reef-icp-target-patch]")) return;

  const style = root.ownerDocument.createElement("style");
  style.dataset.reefIcpTargetPatch = REEF_ICP_TARGET_PATCH_VERSION;
  style.textContent = `
    .status-strip {
      flex-wrap: wrap;
    }

    .reef-icp-laboratory-target {
      opacity: 0.72;
    }

    .reef-icp-personal-state {
      display: inline-flex;
      align-items: center;
      font-size: 0.7rem;
      font-weight: 700;
    }

    .reef-icp-personal-state.low,
    .reef-icp-personal-state.high {
      color: var(--warning-color, #f9a825);
    }

    .reef-icp-custom-target-chip ha-icon {
      color: var(--primary-color);
    }
  `;
  root.append(style);
}

function reefIcpDecorateCard(card) {
  const state = card?._lastState;
  const measurements = Array.isArray(state?.attributes?.measurements)
    ? state.attributes.measurements
    : [];
  if (!measurements.length) return;

  const language = reefIcpPatchLanguage(card);
  reefIcpInstallPatchStyles(card);
  reefIcpDecorateUnknownCounts(card, measurements, language);
  reefIcpDecoratePersonalTargets(card, measurements, language);
}

customElements.whenDefined("reef-icp-card").then(() => {
  const Card = customElements.get("reef-icp-card");
  if (!Card || Card.prototype.__reefIcpTargetPatchInstalled) return;

  const originalRender = Card.prototype._render;
  Card.prototype._render = function (...args) {
    const result = originalRender.apply(this, args);
    reefIcpDecorateCard(this);
    return result;
  };
  Card.prototype.__reefIcpTargetPatchInstalled = true;

  document.querySelectorAll("reef-icp-card").forEach((card) => {
    if (typeof card._render === "function") card._render();
  });
});

customElements.whenDefined("reef-icp-history-card").then(() => {
  const HistoryCard = customElements.get("reef-icp-history-card");
  if (!HistoryCard || HistoryCard.prototype.__reefIcpTargetPatchInstalled) {
    return;
  }

  const originalConfigure = HistoryCard.prototype.configure;
  HistoryCard.prototype.configure = function (options) {
    const measurement = options?.measurement;
    if (measurement?.custom_target) {
      return originalConfigure.call(this, {
        ...options,
        measurement: {
          ...measurement,
          laboratory_target:
            measurement.laboratory_target || measurement.target,
          target: measurement.custom_target,
        },
      });
    }
    return originalConfigure.call(this, options);
  };

  const originalRender = HistoryCard.prototype._render;
  HistoryCard.prototype._render = function (...args) {
    const result = originalRender.apply(this, args);
    const root = this.shadowRoot;
    const measurement = this._measurement;
    if (!root || !measurement?.laboratory_target) return result;

    const language = this._language === "de" ? "de" : "en";
    const t = reefIcpPatchText(language);
    const hint = root.querySelector(".target-hint span");
    if (hint) {
      hint.textContent = `${t.personalTarget}: ${reefIcpPatchTarget(
        measurement.target,
        measurement.unit,
        language
      )}`;
      const container = hint.closest(".target-hint");
      if (
        container &&
        !root.querySelector(".reef-icp-history-laboratory-target")
      ) {
        const lab = root.ownerDocument.createElement("div");
        lab.className =
          "target-hint reef-icp-history-laboratory-target";
        lab.innerHTML =
          '<ha-icon icon="mdi:flask-outline"></ha-icon>' +
          `<span>${t.laboratoryTarget}: ${reefIcpPatchTarget(
            measurement.laboratory_target,
            measurement.unit,
            language
          )}</span>`;
        container.insertAdjacentElement("afterend", lab);
      }
    }
    return result;
  };

  HistoryCard.prototype.__reefIcpTargetPatchInstalled = true;
});
