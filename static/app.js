const bootstrap = window.APP_BOOTSTRAP;

const state = {
  selectedVehicle: bootstrap.defaults.vehicle,
  selectedState: bootstrap.defaults.state,
  selectedDate: bootstrap.defaults.date,
  lastQuote: null,
  requestController: null,
  sliderRefreshTimer: null,
};

const regionColors = {
  new_england: "#6cc6ff",
  central_atlantic: "#4f9dff",
  lower_atlantic: "#5fd7d2",
  midwest: "#7fd8a1",
  gulf_coast: "#16c2a3",
  rocky_mountain: "#2aa8ff",
  west_coast: "#7e91ff",
};

const vehicleGallery = document.getElementById("vehicle-gallery");
const tileMap = document.getElementById("tile-map");
const stateSelect = document.getElementById("state-select");
const dateInput = document.getElementById("date-input");
const dateSlider = document.getElementById("date-slider");
const dateSliderDisplay = document.getElementById("date-slider-display");
const dateSliderCaption = document.getElementById("date-slider-caption");
const dateSliderMinLabel = document.getElementById("date-slider-min-label");
const dateSliderMaxLabel = document.getElementById("date-slider-max-label");
const dateStepBack = document.getElementById("date-step-back");
const dateStepForward = document.getElementById("date-step-forward");
const sourcePill = document.getElementById("source-pill");
const heroVisual = document.getElementById("hero-visual");
const heroSummary = document.getElementById("hero-summary");
const totalCost = document.getElementById("total-cost");
const totalCostDelta = document.getElementById("total-cost-delta");
const pricePerGallon = document.getElementById("price-per-gallon");
const pricePerGallonDelta = document.getElementById("price-per-gallon-delta");
const tankCapacity = document.getElementById("tank-capacity");
const tankCapacityLabel = document.getElementById("tank-capacity-label");
const tankLiquid = document.getElementById("tank-liquid");
const vehicleName = document.getElementById("vehicle-name");
const stateName = document.getElementById("state-name");
const fuelType = document.getElementById("fuel-type");
const sourceTitle = document.getElementById("source-title");
const sourceDetail = document.getElementById("source-detail");
const sourceLinks = document.getElementById("source-links");
const sourceNote = document.getElementById("source-note");
const rootStyle = document.documentElement.style;

const vehicleMap = Object.fromEntries(bootstrap.vehicles.map((vehicle) => [vehicle.id, vehicle]));
const statesByCode = Object.fromEntries(bootstrap.states.map((item) => [item.code, item]));
const MS_PER_DAY = 86_400_000;
const minDateStamp = parseIsoDate(bootstrap.defaults.minDate);
const maxDateStamp = parseIsoDate(bootstrap.defaults.maxDate);
const totalSliderDays = Math.round((maxDateStamp - minDateStamp) / MS_PER_DAY);

init();

function init() {
  renderVehicleGallery();
  renderStateSelect();
  renderTileMap();
  wireControls();
  wireParallax();
  initDateSlider();
  syncSelectionUI();
  refreshQuote();
}

function renderVehicleGallery() {
  vehicleGallery.innerHTML = "";
  bootstrap.vehicles.forEach((vehicle) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "vehicle-card";
    button.dataset.vehicle = vehicle.id;
    button.innerHTML = `
      <div class="vehicle-icon">${buildVehicleSvg(vehicle.silhouette, vehicle.accent)}</div>
      <span class="vehicle-name">${vehicle.name}</span>
      <div class="vehicle-meta">
        <span>${vehicle.tankCapacity.toFixed(1)} gal</span>
        <span>${titleCase(vehicle.fuelType)}</span>
      </div>
      <p class="vehicle-tagline">${vehicle.tagline}</p>
    `;
    button.addEventListener("click", () => {
      state.selectedVehicle = vehicle.id;
      syncSelectionUI();
      refreshQuote();
    });
    vehicleGallery.appendChild(button);
  });
  syncSelectionUI();
}

function renderStateSelect() {
  stateSelect.innerHTML = "";
  bootstrap.states.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.code;
    option.textContent = item.name;
    stateSelect.appendChild(option);
  });
  stateSelect.value = state.selectedState;
  stateSelect.addEventListener("change", () => {
    state.selectedState = stateSelect.value;
    syncSelectionUI();
    refreshQuote();
  });
}

function renderTileMap() {
  tileMap.innerHTML = "";
  bootstrap.states.forEach((item) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "state-tile";
    button.style.gridRow = String(item.tileRow + 1);
    button.style.gridColumn = String(item.tileColumn + 1);
    button.style.setProperty("--tile-color", regionColors[item.region]);
    button.dataset.state = item.code;
    button.title = item.name;
    button.innerHTML = `<span>${item.code}</span>`;
    button.addEventListener("click", () => {
      state.selectedState = item.code;
      syncSelectionUI();
      refreshQuote();
    });
    tileMap.appendChild(button);
  });
  syncSelectionUI();
}

function wireControls() {
  dateSlider.addEventListener("input", () => {
    state.selectedDate = offsetToIsoDate(Number(dateSlider.value));
    syncDateSliderUI();
    scheduleSliderRefresh();
  });

  dateSlider.addEventListener("change", () => {
    state.selectedDate = offsetToIsoDate(Number(dateSlider.value));
    syncDateSliderUI();
    flushSliderRefresh();
  });

  dateInput.addEventListener("change", () => {
    if (!dateInput.value) {
      return;
    }
    state.selectedDate = clampIsoDate(dateInput.value);
    syncDateSliderUI();
    refreshQuote();
  });

  dateStepBack.addEventListener("click", () => {
    shiftSelectedDate(-1);
  });

  dateStepForward.addEventListener("click", () => {
    shiftSelectedDate(1);
  });
}

function wireParallax() {
  window.addEventListener("pointermove", (event) => {
    const offsetX = (event.clientX / window.innerWidth - 0.5) * 18;
    const offsetY = (event.clientY / window.innerHeight - 0.5) * 18;
    rootStyle.setProperty("--parallax-x", `${offsetX.toFixed(2)}px`);
    rootStyle.setProperty("--parallax-y", `${offsetY.toFixed(2)}px`);
  });

  window.addEventListener("pointerleave", () => {
    rootStyle.setProperty("--parallax-x", "0px");
    rootStyle.setProperty("--parallax-y", "0px");
  });
}

function initDateSlider() {
  dateInput.value = state.selectedDate;
  dateInput.min = bootstrap.defaults.minDate;
  dateInput.max = bootstrap.defaults.maxDate;
  dateSlider.min = "0";
  dateSlider.max = String(totalSliderDays);
  dateSlider.step = "1";
  dateSliderMinLabel.textContent = formatLongDate(bootstrap.defaults.minDate);
  dateSliderMaxLabel.textContent = formatLongDate(bootstrap.defaults.maxDate);
  syncDateSliderUI();
}

function syncDateSliderUI() {
  const offset = isoDateToOffset(state.selectedDate);
  const sliderValue = String(offset);
  dateInput.value = state.selectedDate;
  dateSlider.value = sliderValue;
  dateSliderDisplay.textContent = formatLongDate(state.selectedDate);
  dateSliderCaption.textContent = buildDateSliderCaption(state.selectedDate);
  const progress = totalSliderDays === 0 ? 100 : (offset / totalSliderDays) * 100;
  dateSlider.style.setProperty("--slider-progress", `${progress}%`);
  dateStepBack.disabled = offset <= 0;
  dateStepForward.disabled = offset >= totalSliderDays;
}

function scheduleSliderRefresh() {
  if (state.sliderRefreshTimer) {
    window.clearTimeout(state.sliderRefreshTimer);
  }
  state.sliderRefreshTimer = window.setTimeout(() => {
    state.sliderRefreshTimer = null;
    refreshQuote();
  }, 120);
}

function flushSliderRefresh() {
  if (state.sliderRefreshTimer) {
    window.clearTimeout(state.sliderRefreshTimer);
    state.sliderRefreshTimer = null;
  }
  refreshQuote();
}

function syncSelectionUI() {
  document.querySelectorAll(".vehicle-card").forEach((card) => {
    card.classList.toggle("is-active", card.dataset.vehicle === state.selectedVehicle);
  });

  document.querySelectorAll(".state-tile").forEach((tile) => {
    tile.classList.toggle("is-active", tile.dataset.state === state.selectedState);
  });

  stateSelect.value = state.selectedState;
}

async function refreshQuote() {
  if (!state.selectedDate) {
    return;
  }

  document.getElementById("hero-result").classList.add("is-loading");
  sourcePill.textContent = "Loading quote...";
  totalCostDelta.textContent = "Comparing with today...";
  pricePerGallonDelta.textContent = "Comparing with today...";

  if (state.requestController) {
    state.requestController.abort();
  }

  const todayDate = bootstrap.defaults.maxDate;
  state.requestController = new AbortController();

  try {
    const quoteRequest = fetchQuote(
      {
        vehicle: state.selectedVehicle,
        state: state.selectedState,
        date: state.selectedDate,
      },
      state.requestController.signal,
    );
    const comparisonRequest =
      state.selectedDate === todayDate
        ? Promise.resolve(null)
        : fetchQuote(
            {
              vehicle: state.selectedVehicle,
              state: state.selectedState,
              date: todayDate,
            },
            state.requestController.signal,
          );

    const [quoteResult, comparisonResult] = await Promise.allSettled([
      quoteRequest,
      comparisonRequest,
    ]);
    if (quoteResult.status === "rejected") {
      throw quoteResult.reason;
    }

    const todayQuote =
      comparisonResult.status === "fulfilled" ? comparisonResult.value : null;

    state.lastQuote = quoteResult.value;
    applyQuote(quoteResult.value, todayQuote);
  } catch (error) {
    if (error.name === "AbortError") {
      return;
    }
    showError(error.message);
  } finally {
    document.getElementById("hero-result").classList.remove("is-loading");
  }
}

async function fetchQuote(params, signal) {
  const query = new URLSearchParams(params);
  const response = await fetch(`/api/quote?${query.toString()}`, { signal });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Unable to load quote.");
  }
  return payload;
}

function applyQuote(quote, todayQuote) {
  const vehicle = vehicleMap[quote.vehicle.id];
  const selectedState = statesByCode[quote.requestedState.code];
  const accent = vehicle.accent;

  heroVisual.innerHTML = buildVehicleSvg(vehicle.silhouette, accent, true);
  heroSummary.textContent = buildHeroSummary(quote, todayQuote);
  vehicleName.textContent = vehicle.name;
  stateName.textContent = selectedState.name;
  fuelType.textContent = titleCase(quote.fuelType);
  tankCapacity.textContent = `${quote.tankCapacityGallons.toFixed(1)} gal`;
  tankCapacityLabel.textContent = `${quote.tankCapacityGallons.toFixed(1)} gal tank`;
  sourcePill.textContent = buildHeroBadgeText(quote);
  sourceTitle.textContent = buildSourceTitle(quote);
  sourceDetail.textContent = quote.source.detail;
  sourceNote.textContent = quote.dateNote;
  renderSourceLinks(quote.source.links);
  renderComparison(quote, todayQuote);

  animateNumber(totalCost, quote.totalCost, {
    prefix: "$",
    decimals: 2,
  });
  animateNumber(pricePerGallon, quote.pricePerGallon, {
    prefix: "$",
    decimals: 3,
  });

  const normalizedTank = Math.max(18, Math.min(100, (quote.tankCapacityGallons / 125) * 100));
  tankLiquid.style.width = `${normalizedTank}%`;
  tankLiquid.style.setProperty("--tank-accent", accent);
}

function renderSourceLinks(links) {
  sourceLinks.innerHTML = "";
  links.forEach((link) => {
    const anchor = document.createElement("a");
    anchor.href = link.url;
    anchor.target = "_blank";
    anchor.rel = "noreferrer";
    anchor.textContent = link.label;
    sourceLinks.appendChild(anchor);
  });
}

function showError(message) {
  heroSummary.textContent = message;
  sourcePill.textContent = "Source unavailable";
  sourceTitle.textContent = "Could not load fuel quote";
  sourceDetail.textContent = message;
  sourceNote.textContent = "Try another date or reload the page.";
  sourceLinks.innerHTML = "";
  totalCostDelta.textContent = "Comparison unavailable.";
  pricePerGallonDelta.textContent = "Comparison unavailable.";
}

function animateNumber(element, value, { prefix = "", suffix = "", decimals = 0 } = {}) {
  const previous = Number(element.dataset.value || "0");
  const start = Number.isFinite(previous) ? previous : 0;
  const delta = value - start;
  const duration = 650;
  const startTime = performance.now();

  function tick(now) {
    const progress = Math.min(1, (now - startTime) / duration);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = start + delta * eased;
    element.textContent = `${prefix}${current.toFixed(decimals)}${suffix}`;
    if (progress < 1) {
      requestAnimationFrame(tick);
    } else {
      element.dataset.value = String(value);
    }
  }

  requestAnimationFrame(tick);
}

function titleCase(value) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function buildHeroSummary(quote, todayQuote) {
  if (quote.requestedDate === bootstrap.defaults.maxDate || !todayQuote) {
    return quote.headline;
  }

  const priceDelta = todayQuote.totalCost - quote.totalCost;
  const amount = formatCurrency(Math.abs(priceDelta));
  const requestedDateLabel = formatLongDate(quote.requestedDate);
  const refillContext = `Refilling a ${quote.vehicle.name.toLowerCase()} from 10% to full in ${quote.requestedState.name}`;

  if (Math.abs(priceDelta) < 0.005) {
    return `${refillContext} was about ${formatCurrency(quote.totalCost)} on ${requestedDateLabel}, about the same as today.`;
  }

  const comparisonWord = priceDelta > 0 ? "cheaper" : "more expensive";
  return `${refillContext} was about ${formatCurrency(quote.totalCost)} on ${requestedDateLabel}, about ${amount} ${comparisonWord} than today.`;
}

function renderComparison(quote, todayQuote) {
  if (quote.requestedDate === bootstrap.defaults.maxDate) {
    totalCostDelta.textContent = "This is today's tank total, assuming the tank starts at 10% full.";
    pricePerGallonDelta.textContent = "This is today's price per gallon.";
    return;
  }

  if (!todayQuote) {
    totalCostDelta.textContent = "Today's tank comparison is unavailable.";
    pricePerGallonDelta.textContent = "Today's gallon comparison is unavailable.";
    return;
  }

  const gallonDelta = quote.pricePerGallon - todayQuote.pricePerGallon;
  const totalDelta = quote.totalCost - todayQuote.totalCost;

  pricePerGallonDelta.textContent = buildDeltaLine(gallonDelta, 3, "gallon");
  totalCostDelta.textContent = buildDeltaLine(totalDelta, 2, "refill");
}

function buildHeroBadgeText(quote) {
  const effectiveDate = formatLongDate(quote.effectiveDate);
  if (quote.isEstimated) {
    return `Estimate from week of ${effectiveDate}`;
  }
  return `Data for ${effectiveDate}`;
}

function buildSourceTitle(quote) {
  const labels = quote.source.links.map((link) =>
    link.label === "EIA Gasoline and Diesel Fuel Update" ? "EIA Fuel Update" : link.label,
  );
  const uniqueLabels = [...new Set(labels)];
  return uniqueLabels.join(" + ") || "Fuel data source";
}

function formatSignedCurrency(value, decimals) {
  const prefix = value > 0 ? "+" : value < 0 ? "-" : "";
  return `${prefix}$${Math.abs(value).toFixed(decimals)}`;
}

function formatCurrency(value) {
  return `$${Number(value).toFixed(2)}`;
}

function buildDeltaLine(value, decimals, unit) {
  if (Math.abs(value) < 0.005) {
    return unit === "gallon"
      ? "About the same per gallon as today."
      : "About the same for this refill as today.";
  }
  return unit === "gallon"
    ? `${formatSignedCurrency(value, decimals)}/gal versus today`
    : `${formatSignedCurrency(value, decimals)} per refill versus today`;
}

function formatLongDate(value) {
  const [year, month, day] = value.split("-").map(Number);
  const localDate = new Date(year, month - 1, day);
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(localDate);
}

function parseIsoDate(value) {
  const [year, month, day] = value.split("-").map(Number);
  return Date.UTC(year, month - 1, day);
}

function isoDateToOffset(value) {
  return Math.round((parseIsoDate(value) - minDateStamp) / MS_PER_DAY);
}

function offsetToIsoDate(offset) {
  const clampedOffset = Math.max(0, Math.min(totalSliderDays, offset));
  const nextDate = new Date(minDateStamp + clampedOffset * MS_PER_DAY);
  return nextDate.toISOString().slice(0, 10);
}

function clampIsoDate(value) {
  const stamp = parseIsoDate(value);
  const clampedStamp = Math.max(minDateStamp, Math.min(maxDateStamp, stamp));
  return new Date(clampedStamp).toISOString().slice(0, 10);
}

function shiftSelectedDate(deltaDays) {
  const nextOffset = isoDateToOffset(state.selectedDate) + deltaDays;
  state.selectedDate = offsetToIsoDate(nextOffset);
  syncDateSliderUI();
  refreshQuote();
}

function buildDateSliderCaption(value) {
  if (value === bootstrap.defaults.maxDate) {
    return "Today";
  }

  const daysBack = Math.round((maxDateStamp - parseIsoDate(value)) / MS_PER_DAY);
  if (daysBack < 31) {
    return `${daysBack} day${daysBack === 1 ? "" : "s"} back`;
  }
  if (daysBack < 365) {
    const monthsBack = Math.round(daysBack / 30.4);
    return `${monthsBack} month${monthsBack === 1 ? "" : "s"} back`;
  }
  const yearsBack = Math.round(daysBack / 365.25);
  return `${yearsBack} year${yearsBack === 1 ? "" : "s"} back`;
}

function buildVehicleSvg(kind, accent, large = false) {
  const width = large ? 360 : 132;
  const height = large ? 190 : 74;
  const stroke = "#10203f";
  const wheel = (cx, cy, r) => `
    <circle cx="${cx}" cy="${cy}" r="${r}" fill="${stroke}"></circle>
    <circle cx="${cx}" cy="${cy}" r="${r * 0.46}" fill="#fff6e9"></circle>
  `;

  const bodies = {
    scooter: `
      <circle cx="126" cy="86" r="12" fill="#ffeccc" stroke="${stroke}" stroke-width="8"></circle>
      <path d="M126 98 L146 116 L188 116 L210 90 L232 90" fill="none" stroke="${stroke}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"></path>
      <path d="M170 54 L194 54 L208 90 L186 114 L152 114 L138 90 Z" fill="${accent}" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <path d="M200 56 L222 48 L232 54" fill="none" stroke="${stroke}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"></path>
      <path d="M152 118 L114 118" fill="none" stroke="${stroke}" stroke-width="8" stroke-linecap="round"></path>
    `,
    motorcycle: `
      <path d="M118 116 L148 86 L184 86 L214 112 L246 96" fill="none" stroke="${stroke}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"></path>
      <path d="M152 60 L192 60 L206 84 L160 84 Z" fill="${accent}" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <path d="M198 60 L218 50 L232 58" fill="none" stroke="${stroke}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"></path>
      <path d="M170 88 L154 114 L200 114 L214 92" fill="none" stroke="${stroke}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"></path>
      <path d="M144 114 L112 114" fill="none" stroke="${stroke}" stroke-width="8" stroke-linecap="round"></path>
    `,
    touring_bike: `
      <path d="M108 118 L146 88 L196 88 L226 112 L258 96" fill="none" stroke="${stroke}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"></path>
      <path d="M146 62 L198 62 L214 86 L152 86 Z" fill="${accent}" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <path d="M202 62 L226 52 L242 60" fill="none" stroke="${stroke}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"></path>
      <path d="M162 90 L146 116 L214 116 L226 94" fill="none" stroke="${stroke}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"></path>
      <rect x="198" y="70" width="34" height="22" rx="5" fill="#fff4e1" stroke="${stroke}" stroke-width="8"></rect>
      <rect x="134" y="70" width="24" height="20" rx="5" fill="#ffe7c9" stroke="${stroke}" stroke-width="8"></rect>
    `,
    hatchback: `
      <path d="M48 112 L98 70 L196 70 L236 92 L274 92 L294 112 L300 132 L40 132 Z" fill="${accent}" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <path d="M114 72 L150 72 L140 102 L82 102 Z" fill="#ffe8c7" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <path d="M154 72 L192 72 L226 100 L150 100 Z" fill="#fff2dd" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
    `,
    coupe: `
      <path d="M46 116 L112 74 L205 74 L255 106 L300 106 L314 132 L38 132 Z" fill="${accent}" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <path d="M128 76 L188 76 L226 104 L104 104 Z" fill="#fff0d8" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
    `,
    sedan: `
      <path d="M34 116 L84 76 L214 76 L264 102 L314 102 L324 132 L30 132 Z" fill="${accent}" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <path d="M96 78 L154 78 L146 104 L70 104 Z" fill="#ffe9cd" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <path d="M160 78 L220 78 L250 104 L152 104 Z" fill="#fff4e4" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
    `,
    wagon: `
      <path d="M26 112 L66 76 L236 76 L286 94 L320 94 L330 132 L26 132 Z" fill="${accent}" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <path d="M82 78 L138 78 L130 102 L60 102 Z" fill="#ffe9cd" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <path d="M146 78 L222 78 L248 102 L138 102 Z" fill="#fff4e4" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
    `,
    crossover: `
      <path d="M26 112 L76 74 L220 74 L272 98 L316 98 L326 132 L24 132 Z" fill="${accent}" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <path d="M90 76 L150 76 L140 102 L58 102 Z" fill="#ffebd0" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <path d="M156 76 L224 76 L252 102 L146 102 Z" fill="#fff3e1" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
    `,
    minivan: `
      <path d="M18 106 L64 70 L238 70 L286 82 L322 82 L338 132 L22 132 Z" fill="${accent}" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <path d="M78 72 L144 72 L138 98 L48 98 Z" fill="#ffe8c9" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <path d="M150 72 L244 72 L270 98 L142 98 Z" fill="#fff2de" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
    `,
    suv: `
      <path d="M20 108 L68 68 L240 68 L286 90 L324 90 L336 132 L20 132 Z" fill="${accent}" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <path d="M78 70 L148 70 L142 98 L46 98 Z" fill="#ffe5c0" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <path d="M156 70 L246 70 L276 98 L148 98 Z" fill="#fff0d7" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
    `,
    pickup: `
      <path d="M18 112 L66 76 L172 76 L204 96 L258 96 L278 70 L324 70 L338 132 L18 132 Z" fill="${accent}" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <path d="M80 78 L138 78 L132 102 L48 102 Z" fill="#ffe8cb" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <rect x="222" y="78" width="92" height="26" rx="6" fill="#fff3e2" stroke="${stroke}" stroke-width="8"></rect>
    `,
    cargo_van: `
      <path d="M24 104 L86 70 L250 70 L296 82 L326 82 L338 132 L24 132 Z" fill="${accent}" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <path d="M100 72 L168 72 L158 98 L62 98 Z" fill="#ffead0" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <rect x="184" y="72" width="92" height="26" rx="6" fill="#fff4e1" stroke="${stroke}" stroke-width="8"></rect>
    `,
    box_truck: `
      <path d="M36 132 L40 90 L120 90 L150 64 L218 64 L236 90 L302 90 L324 132 Z" fill="${accent}" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <rect x="120" y="44" width="150" height="54" rx="8" fill="#fff2dd" stroke="${stroke}" stroke-width="8"></rect>
      <path d="M154 66 L198 66 L190 90 L136 90 Z" fill="#ffe6c5" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
    `,
    semi: `
      <rect x="138" y="36" width="176" height="74" rx="10" fill="#fff4e0" stroke="${stroke}" stroke-width="8"></rect>
      <path d="M32 132 L38 92 L118 92 L150 58 L220 58 L238 92 L286 92 L302 132 Z" fill="${accent}" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      <path d="M156 60 L202 60 L194 90 L144 90 Z" fill="#ffe7c5" stroke="${stroke}" stroke-width="8" stroke-linejoin="round"></path>
      ${wheel(100, 140, 18)}
      ${wheel(236, 140, 18)}
      ${wheel(282, 140, 18)}
      ${wheel(314, 140, 18)}
    `,
  };

  const frontBumper = ["semi", "scooter", "motorcycle", "touring_bike"].includes(kind)
    ? ""
    : `<rect x="28" y="126" width="292" height="10" rx="5" fill="#10203f" opacity="0.14"></rect>`;
  const standardWheels = ["semi", "scooter", "motorcycle", "touring_bike"].includes(kind)
    ? ""
    : `${wheel(96, 140, 18)}${wheel(258, 140, 18)}`;
  const motorcycleWheels = kind === "scooter"
    ? `${wheel(122, 136, 16)}${wheel(242, 136, 16)}`
    : ["motorcycle", "touring_bike"].includes(kind)
      ? `${wheel(118, 136, 18)}${wheel(254, 136, 18)}`
      : "";

  return `
    <svg viewBox="0 0 360 170" width="${width}" height="${height}" role="img" aria-label="${kind}">
      <ellipse cx="188" cy="150" rx="134" ry="12" fill="rgba(16, 32, 63, 0.12)"></ellipse>
      ${bodies[kind]}
      ${frontBumper}
      ${standardWheels}
      ${motorcycleWheels}
    </svg>
  `;
}
