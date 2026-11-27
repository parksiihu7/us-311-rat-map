/* US Rat Complaint Atlas — client
   Loads compact per-city/per-year chunks produced by scripts/fetch_311.py,
   aggregates them into an adaptive canvas cluster layer, and exports the
   filtered selection as CSV. */

const EPOCH = Date.UTC(2000, 0, 1);
const DAY = 86400000;
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const day2date = (d) => new Date(EPOCH + d * DAY);
const MONTH_LUT = new Int32Array(14000);
for (let i = 0; i < MONTH_LUT.length; i++) {
  const dt = new Date(EPOCH + i * DAY);
  MONTH_LUT[i] = dt.getUTCFullYear() * 12 + dt.getUTCMonth();
}
const iso = (d) => d.toISOString().slice(0, 10);
const date2day = (s) => Math.round((Date.parse(s + "T00:00:00Z") - EPOCH) / DAY);

const CITY_CENTER = {
  nyc: [40.7128, -74.006],
  chicago: [41.8781, -87.6298],
  boston: [42.3601, -71.0589],
  "washington-dc": [38.9072, -77.0369],
  baltimore: [39.2904, -76.6122],
  detroit: [42.3314, -83.0458],
  cincinnati: [39.1031, -84.512],
  pittsburgh: [40.4406, -79.9959],
  cambridge: [42.3736, -71.1097],
  "san-francisco": [37.7749, -122.4194],
  "new-orleans": [29.9511, -90.0715],
  "baton-rouge": [30.4515, -91.1871],
};

/* ---------------------------------------------------------------- standardisation */
const STD = {
  rat: "Rat sighting",
  mouse: "Mouse sighting",
  signs: "Signs of rodent activity",
  dead: "Dead rodent report",
  bite: "Bite / exposure",
  infestation: "Infestation report",
  building: "Building infestation report",
  outdoor: "Outdoor sighting",
  sewer: "Sewer complaint",
  food: "Food-establishment violation",
  treat: "Baiting / treatment request",
  inspect: "Inspection request",
  followup: "Follow-up inspection",
  alley: "Alley concern",
  housing: "Housing inspection request",
  both: "Mosquito + rodent request",
  other: "Rodent complaint (other)",
};

function standardize(slug, orig) {
  const o = (orig || "").toLowerCase();
  if (slug === "nyc") {
    if (o.includes("rat sighting")) return STD.rat;
    if (o.includes("mouse sighting")) return STD.mouse;
    if (o.includes("signs of rodent")) return STD.signs;
    if (o.includes("bite")) return STD.bite;
    return STD.other;
  }
  if (slug === "chicago") return STD.treat;
  if (slug === "boston") {
    if (o.includes("rodent activity")) return STD.rat;
    if (o.includes("rodent control")) return STD.inspect;
    return STD.other;
  }
  if (slug === "washington-dc") return STD.inspect;
  if (slug === "baltimore") {
    if (o.includes("proactive")) return STD.treat;
    if (o.includes("follow-up")) return STD.followup;
    if (o.includes("alley")) return STD.alley;
    if (o.includes("hcd-rodents")) return STD.housing;
    return STD.treat;
  }
  if (slug === "detroit") return STD.treat;
  if (slug === "cincinnati") {
    if (o.includes("food operation")) return STD.food;
    if (o.includes("sewer")) return STD.sewer;
    if (o.includes("in a building") || o.includes("in  bldg") || o.includes("in or around")) return STD.building;
    if (o.includes("outside")) return STD.outdoor;
    return STD.infestation;
  }
  if (slug === "pittsburgh") return STD.inspect;
  if (slug === "cambridge") {
    if (o.includes("dead")) return STD.dead;
    if (o.includes("sighting")) return STD.rat;
    return STD.other;
  }
  if (slug === "baton-rouge") return o.startsWith("both") ? STD.both : STD.treat;
  return STD.other;
}

/* ---------------------------------------------------------------- state */
const S = {
  manifest: null,
  cities: new Set(),
  from: null,
  to: null,
  chunks: new Map(),       // "slug:year" -> chunk
  pending: new Map(),      // key -> Promise
  needed: 0,
  done: 0,
  renderQueued: false,
  lastCells: null,
  lastMeta: null,
  exporting: false,
};

const map = L.map("map", { zoomControl: false, preferCanvas: true, worldCopyJump: true }).setView([38.2, -96.5], 4);
L.control.zoom({ position: "bottomright" }).addTo(map);

const baseLayers = {
  "Light (Esri)": L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}", {
    attribution: "Tiles &copy; Esri &mdash; Esri, HERE, Garmin, &copy; OpenStreetMap contributors", maxZoom: 19,
  }).addTo(map),
  "Streets (OSM)": L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; OpenStreetMap contributors', maxZoom: 19,
  }),
  "Satellite (Esri)": L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
    attribution: "Tiles &copy; Esri, Maxar, Earthstar Geographics", maxZoom: 19,
  }),
};

/* ---------------------------------------------------------------- canvas cluster layer */
const Cluster = L.Layer.extend({
  initialize() { this._canvas = null; },
  onAdd(m) {
    this._map = m;
    const c = document.createElement("canvas");
    c.className = "cluster-canvas";
    this._canvas = c;
    m.getPanes().overlayPane.appendChild(c);
    m.on("moveend zoomend resize", this._reset, this);
    m.on("movestart zoomstart", () => { if (this._canvas) this._canvas.style.opacity = "0.35"; });
    m.on("moveend zoomend", () => { if (this._canvas) this._canvas.style.opacity = "1"; });
    this._reset();
  },
  onRemove(m) {
    m.off("moveend zoomend resize", this._reset, this);
    if (this._canvas) this._canvas.remove();
  },
  _reset() {
    const size = this._map.getSize();
    const tl = this._map.containerPointToLayerPoint([0, 0]);
    L.DomUtil.setPosition(this._canvas, tl);
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    this._canvas.width = Math.round(size.x * dpr);
    this._canvas.height = Math.round(size.y * dpr);
    this._canvas.style.width = size.x + "px";
    this._canvas.style.height = size.y + "px";
    this._dpr = dpr;
    render();
  },
});

const clusterLayer = new Cluster().addTo(map);

/* city labels */
const labelLayer = L.layerGroup().addTo(map);
function buildLabels() {
  labelLayer.clearLayers();
  for (const c of S.manifest.cities) {
    const center = CITY_CENTER[c.slug];
    if (!center) continue;
    const m = L.circleMarker(center, {
      radius: 3, color: "#0f5132", weight: 1.5, fillColor: "#fff", fillOpacity: 1,
    });
    m.bindTooltip(`${c.short}`, { permanent: true, direction: "right", offset: [6, 0], className: "city-label" });
    labelLayer.addLayer(m);
  }
}
L.control.layers(baseLayers, { "City labels": labelLayer }, { position: "topright", collapsed: true }).addTo(map);

/* ---------------------------------------------------------------- data loading */
async function loadChunk(slug, year) {
  const key = `${slug}:${year}`;
  if (S.chunks.has(key)) return S.chunks.get(key);
  if (S.pending.has(key)) return S.pending.get(key);
  const p = (async () => {
    const url = `data/${slug}/${year}.json`;
    const r = await fetch(url, { cache: "force-cache" });
    if (!r.ok) throw new Error(`${url} ${r.status}`);
    const j = await r.json();
    const rows = j.rows || [];
    const n = rows.length;
    const nx = new Float32Array(n), ny = new Float32Array(n);
    const days = new Int32Array(n), types = new Uint8Array(n);
    for (let i = 0; i < n; i++) {
      const row = rows[i];
      const lat = row[1], lon = row[2];
      nx[i] = (lon + 180) / 360;
      const rad = (lat * Math.PI) / 180;
      ny[i] = (1 - Math.log(Math.tan(rad) + 1 / Math.cos(rad)) / Math.PI) / 2;
      days[i] = row[0];
      types[i] = row[3];
    }
    const chunk = { slug, year, n, nx, ny, days, types };
    S.chunks.set(key, chunk);
    return chunk;
  })();
  S.pending.set(key, p);
  try {
    return await p;
  } finally {
    S.pending.delete(key);
  }
}

function neededKeys() {
  const keys = [];
  const fy = S.from.getUTCFullYear(), ty = S.to.getUTCFullYear();
  for (const c of S.manifest.cities) {
    if (!S.cities.has(c.slug)) continue;
    for (const yStr of Object.keys(c.years)) {
      const y = +yStr;
      if (y < fy || y > ty) continue;
      if (!c.years[yStr]) continue;
      keys.push([c.slug, y]);
    }
  }
  // newest first so the map fills with current data first
  keys.sort((a, b) => b[1] - a[1]);
  return keys;
}

let loadToken = 0;
async function syncData() {
  const token = ++loadToken;
  const keys = neededKeys();
  S.needed = keys.length;
  S.done = 0;
  const bar = document.getElementById("loadbar");
  const txt = document.getElementById("loadtext");
  const showBar = () => { bar.classList.add("show"); txt.textContent = `loading ${S.done}/${S.needed} city-years…`; };
  if (keys.length) showBar();
  const queue = keys.slice();
  const workers = Array.from({ length: 5 }, async () => {
    while (queue.length) {
      if (token !== loadToken) return;
      const [slug, year] = queue.shift();
      const key = `${slug}:${year}`;
      if (S.chunks.has(key)) { S.done++; continue; }
      try {
        await loadChunk(slug, year);
      } catch (e) {
        console.error(e);
      }
      S.done++;
      if (token === loadToken) { showBar(); scheduleRender(); }
    }
  });
  await Promise.all(workers);
  if (token === loadToken) {
    bar.classList.remove("show");
    scheduleRender();
  }
}

function scheduleRender() {
  if (S.renderQueued) return;
  S.renderQueued = true;
  requestAnimationFrame(() => {
    S.renderQueued = false;
    render();
  });
}

/* ---------------------------------------------------------------- render */
const COLORS = [[253, 230, 138], [245, 158, 11], [185, 28, 28]];
function colorFor(t) {
  const x = Math.min(1, Math.max(0, t));
  const seg = x < 0.5 ? 0 : 1;
  const f = x < 0.5 ? x / 0.5 : (x - 0.5) / 0.5;
  const a = COLORS[seg], b = COLORS[seg + 1];
  return `rgb(${Math.round(a[0] + (b[0] - a[0]) * f)},${Math.round(a[1] + (b[1] - a[1]) * f)},${Math.round(a[2] + (b[2] - a[2]) * f)})`;
}

function render() {
  if (!S.manifest || !S.from || !S.to) return;
  const canvas = clusterLayer._canvas;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const dpr = clusterLayer._dpr || 1;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const w = canvas.width / dpr, h = canvas.height / dpr;
  ctx.clearRect(0, 0, w, h);

  const zoom = map.getZoom();
  const scale = 256 * Math.pow(2, zoom);
  const bounds = map.getPixelBounds();
  const bx = bounds.min.x, by = bounds.min.y;
  const pad = 40;
  const cellPx = zoom >= 14 ? 3 : zoom >= 12 ? 4 : zoom >= 10 ? 6 : zoom >= 8 ? 8 : 10;
  const cols = Math.ceil((w + pad * 2) / cellPx) + 1;
  const rows = Math.ceil((h + pad * 2) / cellPx) + 1;

  const fromDay = date2day(iso(S.from));
  const toDay = date2day(iso(S.to));
  const cells = new Map();
  const monthCounts = new Map();
  const cityCounts = new Map();
  typeCountsByCity.clear();
  let total = 0;
  let minD = Infinity, maxD = -Infinity;

  for (const chunk of S.chunks.values()) {
    if (!S.cities.has(chunk.slug)) continue;
    const inYear = chunk.year >= S.from.getUTCFullYear() && chunk.year <= S.to.getUTCFullYear();
    if (!inYear) continue;
    const { n, nx, ny, days, types } = chunk;
    for (let i = 0; i < n; i++) {
      const d = days[i];
      if (d < fromDay || d > toDay) continue;
      const x = nx[i] * scale - bx;
      const y = ny[i] * scale - by;
      if (x >= -pad && y >= -pad && x <= w + pad && y <= h + pad) {
        const cx = (x / cellPx) | 0, cy = (y / cellPx) | 0;
        const k = cy * cols + cx;
        let cell = cells.get(k);
        if (!cell) { cell = { x: cx * cellPx + cellPx / 2, y: cy * cellPx + cellPx / 2, n: 0, t: null, d0: d, d1: d }; cells.set(k, cell); }
        cell.n++;
        if (d < cell.d0) cell.d0 = d;
        if (d > cell.d1) cell.d1 = d;
        if (cell.n <= 400) {
          if (!cell.t) cell.t = {};
          cell.t[types[i]] = (cell.t[types[i]] || 0) + 1;
        }
      }
      total++;
      if (d < minD) minD = d;
      if (d > maxD) maxD = d;
      const mk = MONTH_LUT[d] !== undefined ? MONTH_LUT[d] : 0;
      monthCounts.set(mk, (monthCounts.get(mk) || 0) + 1);
      let tc = typeCountsByCity.get(chunk.slug);
      if (!tc) { tc = new Map(); typeCountsByCity.set(chunk.slug, tc); }
      tc.set(types[i], (tc.get(types[i]) || 0) + 1);
      cityCounts.set(chunk.slug, (cityCounts.get(chunk.slug) || 0) + 1);
    }
  }

  let maxCell = 1;
  const arr = [];
  for (const cell of cells.values()) { if (cell.n > maxCell) maxCell = cell.n; arr.push(cell); }
  arr.sort((a, b) => a.n - b.n);
  const logMax = Math.log(1 + maxCell);

  for (const cell of arr) {
    const t = Math.log(1 + cell.n) / logMax;
    const r = cell.n === 1 ? 1.6 : 2.4 + 9 * Math.sqrt(t);
    ctx.beginPath();
    ctx.arc(cell.x, cell.y, r, 0, Math.PI * 2);
    ctx.fillStyle = colorFor(t);
    ctx.globalAlpha = cell.n === 1 ? 0.55 : 0.72;
    ctx.fill();
  }
  ctx.globalAlpha = 1;

  S.lastCells = { cells, cellPx, cols, bx, by, scale, w, h, pad, maxCell };
  S.lastMeta = { total, minD, maxD, monthCounts, cityCounts, maxCell, zoom };
  updateStats();
}

/* click → cell popup */
map.on("click", (e) => {
  const m = S.lastMeta;
  if (!m || !S.lastCells) return;
  const p = map.latLngToContainerPoint(e.latlng);
  const { cellPx, cols, bx, by, scale, cells } = S.lastCells;
  const zoom = map.getZoom();
  const worldP = map.project(e.latlng, zoom);
  const cx = Math.floor((worldP.x - bx) / cellPx);
  const cy = Math.floor((worldP.y - by) / cellPx);
  const cell = cells.get(cy * cols + cx);
  if (!cell) return;
  const city = dominantCity(e.latlng);
  const typeRows = cell.t ? Object.entries(cell.t).sort((a, b) => b[1] - a[1]).slice(0, 4) : [];
  const labels = city ? S.manifest.byCity.get(city).types : [];
  const rowsHtml = typeRows.map(([i, n]) => {
    const lab = standardize(city, labels[+i] || "");
    return `<li>${lab} <span class="muted">· ${n.toLocaleString()}</span></li>`;
  }).join("");
  const html = `<div class="pop"><h4>${cell.n.toLocaleString()} complaint${cell.n > 1 ? "s" : ""} in this cell</h4>
    <div class="muted">${iso(day2date(cell.d0))} → ${iso(day2date(cell.d1))}</div>
    ${rowsHtml ? `<ul>${rowsHtml}</ul>` : ""}
    <div class="muted" style="margin-top:6px">Zoom in to split this cluster.</div></div>`;
  L.popup({ maxWidth: 260 }).setLatLng(e.latlng).setContent(html).openOn(map);
});

function dominantCity(latlng) {
  let best = null, bestD = Infinity;
  for (const [slug, c] of Object.entries(CITY_CENTER)) {
    if (!S.cities.has(slug)) continue;
    const d = (c[0] - latlng.lat) ** 2 + (c[1] - latlng.lng) ** 2;
    if (d < bestD) { bestD = d; best = slug; }
  }
  return best;
}

/* ---------------------------------------------------------------- stats */
function fmt(n) { return n.toLocaleString("en-US"); }

function updateStats() {
  const m = S.lastMeta;
  const totalEl = document.getElementById("stat-total");
  if (!m) return;
  totalEl.textContent = fmt(m.total);
  const cityN = [...S.cities].length;
  const d0 = m.total ? iso(day2date(m.minD)) : "—";
  const d1 = m.total ? iso(day2date(m.maxD)) : "—";
  document.getElementById("stat-sub").innerHTML =
    `${cityN} cit${cityN === 1 ? "y" : "ies"} · ${d0} → ${d1}<br>
     <b>${fmt(m.maxCell)}</b> in the largest cluster`;

  // monthly sparkline
  drawSpark(m.monthCounts);

  // type mix (type indices are city-local, so map through each city's labels)
  const rows = [...typeCountsByCity.entries()]
    .filter(([slug]) => S.cities.has(slug))
    .flatMap(([slug, mapT]) => [...mapT.entries()].map(([ti, n]) => [standardize(slug, S.manifest.byCity.get(slug).types[ti] || ""), n]));
  const agg = new Map();
  for (const [lab, n] of rows) agg.set(lab, (agg.get(lab) || 0) + n);
  const top = [...agg.entries()].sort((a, b) => b[1] - a[1]).slice(0, 7);
  document.getElementById("type-mix").innerHTML = top.length
    ? `<div class="sub" style="margin:0 0 2px">What the reports actually say</div>` +
      top.map(([lab, n]) => `<div class="mix-row"><span>${lab}</span><span class="v">${fmt(n)}</span></div>`).join("")
    : "";

  // city bars
  const bars = [...S.cities].map((slug) => [slug, m.cityCounts.get(slug) || 0]).sort((a, b) => b[1] - a[1]);
  const max = Math.max(1, ...bars.map((b) => b[1]));
  document.getElementById("city-bars").innerHTML = bars.map(([slug, n]) => {
    const c = S.manifest.byCity.get(slug);
    return `<div class="bar-row" title="${c.source_name}">
      <span class="lab">${c.short}</span>
      <span class="track"><span class="fill" style="width:${(n / max) * 100}%"></span></span>
      <span class="num">${fmt(n)}</span></div>`;
  }).join("");

  // export note
  const note = document.getElementById("export-note");
  note.innerHTML = `${fmt(m.total)} geolocated rows will be written with date, city, coordinates,
    standardized type and the city's original classification.`;
}

/* populated during the render loop (per-city type histograms) */
const typeCountsByCity = new Map();

function drawSpark(monthCounts) {
  const cv = document.getElementById("spark");
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const w = cv.clientWidth, h = 74;
  cv.width = w * dpr; cv.height = h * dpr;
  const ctx = cv.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  if (!monthCounts.size) return;
  const keys = [...monthCounts.keys()].sort((a, b) => a - b);
  const start = date2day(iso(S.from)), end = date2day(iso(S.to));
  const m0 = new Date(EPOCH + start * DAY), m1 = new Date(EPOCH + end * DAY);
  const k0 = m0.getUTCFullYear() * 12 + m0.getUTCMonth();
  const k1 = m1.getUTCFullYear() * 12 + m1.getUTCMonth();
  const n = Math.max(1, k1 - k0 + 1);
  const vals = new Array(n).fill(0);
  for (const [k, v] of monthCounts) if (k >= k0 && k <= k1) vals[k - k0] += v;
  const max = Math.max(1, ...vals);
  const bw = w / n;
  for (let i = 0; i < n; i++) {
    const bh = (vals[i] / max) * (h - 12);
    ctx.fillStyle = "#0f5132";
    ctx.globalAlpha = 0.25 + 0.65 * (vals[i] / max);
    ctx.fillRect(i * bw, h - bh - 2, Math.max(1, bw - 0.8), bh);
  }
  ctx.globalAlpha = 1;
  ctx.fillStyle = "#9ca3af";
  ctx.font = "9px Inter, sans-serif";
  const y0 = Math.floor(k0 / 12), y1 = Math.floor(k1 / 12);
  const years = y1 - y0 + 1;
  const step = Math.max(1, Math.ceil(years / 6));
  for (let y = y0; y <= y1; y++) {
    const x = ((y * 12 - k0) / n) * w;
    if (x < -2 || x > w - 10) continue;
    ctx.fillRect(x, 0, 0.5, h);
    if ((y - y0) % step === 0) ctx.fillText(String(y), x + 2, 8);
  }
}

/* ---------------------------------------------------------------- filters UI */
function buildCityList() {
  const el = document.getElementById("city-list");
  el.innerHTML = "";
  const list = [...S.manifest.cities].sort((a, b) => b.n - a.n);
  for (const c of list) {
    const row = document.createElement("label");
    row.className = "city-row";
    row.innerHTML = `<input type="checkbox" ${S.cities.has(c.slug) ? "checked" : ""} data-slug="${c.slug}">
      <span class="nm">${c.city} <span class="st">${c.state}</span></span>
      <span class="ct">${fmt(c.n)}</span>`;
    row.querySelector("input").addEventListener("change", (e) => {
      if (e.target.checked) S.cities.add(c.slug); else S.cities.delete(c.slug);
      afterFilterChange();
    });
    el.appendChild(row);
  }
}

function afterFilterChange() {
  saveUrl();
  syncData();
  scheduleRender();
}

function setRange(months, all) {
  const today = new Date();
  const t = iso(new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate())));
  let f;
  if (all) {
    f = S.manifest.dateMin;
  } else {
    const d = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth() - months, today.getUTCDate()));
    f = iso(d);
  }
  S.from = new Date(f + "T00:00:00Z");
  S.to = new Date(t + "T00:00:00Z");
  document.getElementById("from").value = f;
  document.getElementById("to").value = t;
}

function initRangeInputs() {
  const f = document.getElementById("from"), t = document.getElementById("to");
  f.min = S.manifest.dateMin; f.max = S.manifest.dateMax;
  t.min = S.manifest.dateMin; t.max = S.manifest.dateMax;
  f.addEventListener("change", () => { if (f.value) { S.from = new Date(f.value + "T00:00:00Z"); afterFilterChange(); } });
  t.addEventListener("change", () => { if (t.value) { S.to = new Date(t.value + "T00:00:00Z"); afterFilterChange(); } });
  document.getElementById("range-presets").addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    setRange(+b.dataset.range || 0, b.dataset.range === "all");
    afterFilterChange();
  });
  document.getElementById("city-presets").addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    const mode = b.dataset.cities;
    S.cities.clear();
    if (mode === "all") S.manifest.cities.forEach((c) => S.cities.add(c.slug));
    if (mode === "big") ["nyc", "chicago", "washington-dc", "baltimore", "boston", "detroit"].forEach((s) => S.cities.add(s));
    buildCityList();
    afterFilterChange();
  });
}

/* ---------------------------------------------------------------- CSV */
function csvField(v) {
  const s = v == null ? "" : String(v);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

const ISO_LUT = [];
function isoOfDay(d) {
  let v = ISO_LUT[d];
  if (v === undefined) { v = iso(day2date(d)); ISO_LUT[d] = v; }
  return v;
}

/* CSV export is a resumable job: one part is built per click so a large
   selection never has to sit in memory as one giant blob. */
const CHUNK = 100000;
const EXPORT = { job: null };

function csvRowCount() {
  const fromDay = date2day(iso(S.from)), toDay = date2day(iso(S.to));
  let n = 0;
  for (const [slug, year] of neededKeys()) {
    const ch = S.chunks.get(`${slug}:${year}`);
    if (!ch) continue;
    for (let i = 0; i < ch.n; i++) { const d = ch.days[i]; if (d >= fromDay && d <= toDay) n++; }
  }
  return n;
}

async function startExport() {
  if (EXPORT.job) return;
  const btn = document.getElementById("btn-csv");
  const note = document.getElementById("export-note");
  const fb = document.getElementById("save-fallback");
  btn.disabled = true;
  fb.innerHTML = "";
  note.textContent = "loading remaining city-years…";
  await syncData();
  const total = csvRowCount();
  EXPORT.job = {
    keys: neededKeys(), ki: 0, ri: 0, written: 0, part: 1,
    total, files: Math.max(1, Math.ceil(total / CHUNK)),
    fromDay: date2day(iso(S.from)), toDay: date2day(iso(S.to)),
  };
  note.textContent = `${fmt(total)} rows — building part 1 of ${EXPORT.job.files}…`;
  await stepExport();
}

async function stepExport() {
  const j = EXPORT.job;
  if (!j) return;
  const btn = document.getElementById("btn-csv");
  const note = document.getElementById("export-note");
  const fb = document.getElementById("save-fallback");
  btn.disabled = true;
  const lines = ["complaint_date,city,state,latitude,longitude,standardized_type,original_classification,data_source,source_dataset\n"];
  let count = 0;
  let done = false;
  while (j.ki < j.keys.length) {
    const [slug, year] = j.keys[j.ki];
    const ch = S.chunks.get(`${slug}:${year}`);
    if (!ch) { j.ki++; j.ri = 0; continue; }
    const meta = S.manifest.byCity.get(slug);
    let i = j.ri;
    for (; i < ch.n; i++) {
      const d = ch.days[i];
      if (d < j.fromDay || d > j.toDay) continue;
      const orig = meta.types[ch.types[i]] || "";
      const lat = mercYToLat(ch.ny[i]);
      const lon = ch.nx[i] * 360 - 180;
      if (!isFinite(lat) || !isFinite(lon)) continue;
      lines.push(`${isoOfDay(d)},${csvField(meta.city)},${meta.state},${lat.toFixed(5)},${lon.toFixed(5)},${csvField(standardize(slug, orig))},${csvField(orig)},${csvField(meta.source_name)},${csvField(meta.dataset_ids)}\n`);
      count++; j.written++;
      if (count >= CHUNK) { i++; break; }
    }
    if (count >= CHUNK) { j.ri = i; break; }
    j.ki++; j.ri = 0;
  }
  if (j.ki >= j.keys.length) done = true;

  const name = j.files > 1
    ? `us-rat-complaints_${iso(S.from)}_${iso(S.to)}_part${j.part}of${j.files}.csv`
    : `us-rat-complaints_${iso(S.from)}_${iso(S.to)}.csv`;
  // release the previous part's bytes: only one part is ever held in memory
  if (EXPORT.prevUrl) { URL.revokeObjectURL(EXPORT.prevUrl); EXPORT.prevUrl = null; }
  const blob = new Blob(lines, { type: "text/csv" });
  lines.length = 0;
  const url = URL.createObjectURL(blob);
  EXPORT.prevUrl = url;
  fb.innerHTML = `<a class="btn" id="dl-this" style="display:block;text-align:center;margin-top:8px;text-decoration:none;font-size:11.5px" href="${url}" download="${name}">Save ${name} (${(blob.size / 1e6).toFixed(1)} MB)</a>`;
  const a = document.createElement("a");
  a.href = url; a.download = name; a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  a.remove();

  if (done) {
    note.textContent = `Done — ${fmt(j.written)} rows${j.files > 1 ? ` in ${j.files} files` : ""}. If a download did not start, use the save link.`;
    btn.textContent = "Download CSV for this selection";
    btn.disabled = false;
    EXPORT.job = null;
    return;
  }
  j.part++;
  note.innerHTML = `Part ${j.part - 1} of ${j.files} ready (${fmt(j.written)} of ${fmt(j.total)} rows) — save it before continuing.`;
  btn.textContent = `Continue with part ${j.part} of ${j.files}`;
  btn.disabled = false;
}

function onExportClick() {
  if (EXPORT.job) stepExport(); else startExport();
}

function mercYToLat(ny) {
  const n = Math.PI * (1 - 2 * ny);
  return (Math.atan(Math.sinh(n)) * 180) / Math.PI;
}

/* ---------------------------------------------------------------- URL state */
function saveUrl() {
  const u = new URL(location.href);
  u.searchParams.set("c", [...S.cities].join(","));
  u.searchParams.set("f", iso(S.from));
  u.searchParams.set("t", iso(S.to));
  history.replaceState(null, "", u.toString());
}

function loadUrl() {
  const p = new URL(location.href).searchParams;
  const c = p.get("c");
  if (c !== null) {
    S.cities = new Set(c.split(",").filter((s) => S.manifest.byCity.has(s)));
  } else {
    S.manifest.cities.forEach((x) => S.cities.add(x.slug));
  }
  const lat = parseFloat(p.get("lat")), lng = parseFloat(p.get("lng")), z = parseInt(p.get("z"), 10);
  if (isFinite(lat) && isFinite(lng)) map.setView([lat, lng], isFinite(z) ? z : 11);
  if (p.get("f") && p.get("t")) {
    S.from = new Date(p.get("f") + "T00:00:00Z");
    S.to = new Date(p.get("t") + "T00:00:00Z");
    document.getElementById("from").value = p.get("f");
    document.getElementById("to").value = p.get("t");
  }
}

/* ---------------------------------------------------------------- modal */
function buildSourceTable() {
  const t = document.getElementById("src-table");
  const head = `<thead><tr><th>City</th><th>Dataset</th><th>Filter used</th><th class="n">Records</th>
    <th class="n">No coords</th><th>Dates</th></tr></thead>`;
  const rows = S.manifest.cities.map((c) => `<tr>
    <td><b>${c.city}, ${c.state}</b><br><span style="color:#6b7280">${c.short}</span></td>
    <td><a href="${c.source_url}" target="_blank" rel="noopener">${c.source_name}</a><br>
        <span style="color:#6b7280">${c.dataset_ids}</span></td>
    <td><code style="font-size:11px">${c.filter}</code></td>
    <td class="n">${fmt(c.n)}</td>
    <td class="n">${fmt(c.nocoord)}</td>
    <td>${c.date_min} → ${c.date_max}</td></tr>`).join("");
  t.innerHTML = head + `<tbody>${rows}</tbody>`;
}

/* ---------------------------------------------------------------- boot */
async function boot() {
  const m = await (await fetch("data/manifest.json")).json();
  m.byCity = new Map(m.cities.map((c) => [c.slug, c]));
  S.manifest = m;
  document.getElementById("top-badge").textContent =
    `${m.cities.length} cities · ${(m.total_records / 1e6).toFixed(2)}M reports`;

  const dates = m.cities.map((c) => c.date_min).filter(Boolean).sort();
  m.dateMin = dates[0] || "2012-01-01";
  m.dateMax = iso(new Date());

  setRange(24, false);
  loadUrl();
  buildCityList();
  initRangeInputs();
  buildSourceTable();
  buildLabels();

  document.getElementById("btn-method").addEventListener("click", () => document.getElementById("modal").classList.add("show"));
  document.getElementById("btn-close-modal").addEventListener("click", () => document.getElementById("modal").classList.remove("show"));
  document.getElementById("modal").addEventListener("click", (e) => { if (e.target.id === "modal") e.target.classList.remove("show"); });
  document.getElementById("btn-csv").addEventListener("click", onExportClick);
  document.getElementById("btn-share").addEventListener("click", async (e) => {
    saveUrl();
    try { await navigator.clipboard.writeText(location.href); e.target.textContent = "Link copied"; }
    catch { e.target.textContent = "Copy failed"; }
    setTimeout(() => (e.target.textContent = "Copy link"), 1600);
  });

  map.on("moveend zoomend", scheduleRender);
  saveUrl();
  syncData();
  window.__S = S;
  window.__map = map;
  window.__atlasReady = true;
}

boot().catch((e) => {
  console.error(e);
  document.getElementById("loadtext").textContent = "could not load data";
  document.getElementById("loadbar").classList.add("show");
});
