// Analytics dashboard — read-only, auto-refreshing. No write operations.

const REFRESH_INTERVAL_MS = 10_000;

const $ = (id) => document.getElementById(id);

let selectedOrganismId = null;
let refreshTimer = null;
let allEvents = [];

// ─── Auth ─────────────────────────────────────────────────────────────────────

$("auth-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = $("email").value;
  const password = $("password").value;
  let res = await api("/auth/signup", { method: "POST", body: { email, password, name: "Analyst" } });
  if (!res.ok && res.status === 409) {
    res = await api("/auth/login", { method: "POST", body: { email, password } });
  }
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    showAuthError(detail.detail ? JSON.stringify(detail.detail) : `Error ${res.status}`);
    return;
  }
  await boot();
});

$("sign-out").addEventListener("click", async () => {
  await api("/auth/logout", { method: "POST" });
  clearInterval(refreshTimer);
  $("dashboard").classList.add("hidden");
  $("auth").classList.remove("hidden");
});

function showAuthError(msg) {
  const el = $("auth-error");
  el.textContent = msg;
  el.classList.remove("hidden");
}

// ─── Boot & Refresh ───────────────────────────────────────────────────────────

async function tryAutoLogin() {
  const res = await api("/api/organisms");
  if (res.ok) await boot();
}

async function boot() {
  $("auth").classList.add("hidden");
  $("dashboard").classList.remove("hidden");
  await refresh();
  clearInterval(refreshTimer);
  refreshTimer = setInterval(refresh, REFRESH_INTERVAL_MS);
}

async function refresh() {
  setPulse(true);
  try {
    const [healthRes, orgsRes, contractsRes, requestsRes] = await Promise.all([
      api("/health"),
      api("/api/organisms"),
      api("/api/contracts"),
      api("/api/structure-requests"),
    ]);

    if (orgsRes.status === 401) {
      $("dashboard").classList.add("hidden");
      $("auth").classList.remove("hidden");
      return;
    }

    const health     = healthRes.ok     ? await healthRes.json()     : null;
    const orgsBody   = orgsRes.ok       ? await orgsRes.json()       : { organisms: [] };
    const cBody      = contractsRes.ok  ? await contractsRes.json()  : { contracts: [] };
    const rBody      = requestsRes.ok   ? await requestsRes.json()   : { structure_requests: [] };

    const organisms  = orgsBody.organisms       || [];
    const contracts  = cBody.contracts          || [];
    const requests   = rBody.structure_requests || [];

    updateHealth(health);
    updateSummary(organisms, contracts, requests);
    renderOrganismList(organisms);
    renderContracts(contracts);
    renderRequests(requests);

    if (selectedOrganismId) {
      await refreshOrganism(selectedOrganismId);
    } else if (organisms[0]) {
      selectOrganism(organisms[0].organism_id);
    }

    $("last-refresh").textContent = `updated ${new Date().toLocaleTimeString()}`;
  } finally {
    setPulse(false);
  }
}

async function refreshOrganism(id) {
  const res = await api(`/api/organisms/${id}`);
  if (!res.ok) return;
  const detail = await res.json();
  renderDetail(detail);
  renderEventStream(detail.events || []);
}

function selectOrganism(id) {
  selectedOrganismId = id;
  document.querySelectorAll(".org-item").forEach((el) => {
    el.classList.toggle("selected", el.dataset.id === id);
  });
  refreshOrganism(id);
}

// ─── Health strip ─────────────────────────────────────────────────────────────

function updateHealth(health) {
  if (!health) return;
  const storeTag = $("storage-tag");
  storeTag.textContent = `storage: ${health.storage.mode}`;
  storeTag.className = `tag ${health.storage.degraded ? "warn" : "ok"}`;
  $("runtime-tag").textContent = `runtime: ${health.status}`;
  $("runtime-tag").className = "tag ok";
}

// ─── Summary strip ────────────────────────────────────────────────────────────

function updateSummary(organisms, contracts, requests) {
  const active     = organisms.filter((o) => o.lifecycle_state === "active").length;
  const hibernated = organisms.filter((o) => o.lifecycle_state === "hibernated").length;
  const openReqs   = requests.filter((r) => r.status === "open").length;

  setStatCard("s-organisms", organisms.length, "Organisms");
  setStatCard("s-active",    active,           "Active");
  setStatCard("s-hibernated",hibernated,       "Hibernated");
  setStatCard("s-cells",     "…",              "Cells");
  setStatCard("s-contracts", contracts.filter((c) => c.status === "active").length, "Active Contracts");
  setStatCard("s-requests",  openReqs,         "Open Requests");
  $("s-requests").className = `stat${openReqs > 0 ? " warn" : ""}`;
}

function setStatCard(id, value, label) {
  const el = $(id);
  el.innerHTML = `<span class="n">${escapeHtml(String(value))}</span><span class="l">${escapeHtml(label)}</span>`;
}

// ─── Organism list (left panel) ───────────────────────────────────────────────

function renderOrganismList(organisms) {
  const el = $("organism-list");
  if (!organisms.length) {
    el.innerHTML = `<p class="empty">No organisms</p>`;
    return;
  }
  el.innerHTML = organisms.map((o) => {
    const dot = lifecycleDot(o.lifecycle_state);
    const selected = o.organism_id === selectedOrganismId ? " selected" : "";
    return `<button class="org-item${selected}" data-id="${escapeHtml(o.organism_id)}" type="button">
      <span class="dot ${dot}"></span>
      <span class="org-name">${escapeHtml(o.identity_profile.name)}</span>
      <span class="org-meta">${escapeHtml(o.lifecycle_state)} · ${escapeHtml(o.development_stage)}</span>
    </button>`;
  }).join("");
  el.querySelectorAll(".org-item").forEach((btn) => {
    btn.addEventListener("click", () => selectOrganism(btn.dataset.id));
  });
}

// ─── Organism detail (center panel) ───────────────────────────────────────────

function renderDetail(detail) {
  const o = detail.organism;
  const cells = detail.cells || [];
  const proteins = detail.proteins || [];
  const memory = detail.memory_records || [];
  const structReqs = detail.structure_requests || [];

  $("detail-name").textContent = o.identity_profile.name;
  $("detail-badges").innerHTML = `
    <span class="badge ${lifecycleBadge(o.lifecycle_state)}">${escapeHtml(o.lifecycle_state)}</span>
    <span class="badge neutral">${escapeHtml(o.development_stage)}</span>
  `;

  // Update total cells in summary strip
  setStatCard("s-cells", cells.length, "Cells");

  // Cell health breakdown
  const cellGroups = groupBy(cells, (c) => c.health_state);
  const cellRows = Object.entries(cellGroups)
    .map(([state, list]) => `
      <div class="breakdown-row">
        <span class="dot ${healthDot(state)}"></span>
        <span class="breakdown-label">${escapeHtml(state)}</span>
        <span class="breakdown-count">${list.length}</span>
        <div class="bar-track"><div class="bar-fill ${healthDot(state)}" style="width:${Math.round(list.length / cells.length * 100)}%"></div></div>
      </div>`)
    .join("") || `<p class="empty">No cells</p>`;

  // Protein status distribution (last 20)
  const recentProteins = proteins.slice(-20);
  const proteinGroups = groupBy(recentProteins, (p) => p.status);
  const proteinRows = Object.entries(proteinGroups)
    .map(([status, list]) => `
      <div class="status-row">
        <span class="badge ${proteinBadge(status)}">${escapeHtml(status)}</span>
        <span class="breakdown-count">${list.length}</span>
      </div>`)
    .join("") || `<p class="empty">No proteins</p>`;

  // Genome quick info
  const genome = detail.genome;
  const genomeInfo = genome
    ? `<div class="info-grid">
        <span class="info-label">genome</span><span class="info-value mono">${escapeHtml(genome.genome_id.slice(0, 12))}…</span>
        <span class="info-label">version</span><span class="info-value">v${genome.version}</span>
        <span class="info-label">modules</span><span class="info-value">${genome.modules.length}</span>
        <span class="info-label">instructions</span><span class="info-value">${genome.core_instruction_set.length}</span>
      </div>`
    : `<p class="empty">No genome</p>`;

  $("organism-detail").innerHTML = `
    <div class="detail-sections">

      <div class="detail-section">
        <h3>Identity</h3>
        <div class="info-grid">
          <span class="info-label">purpose</span><span class="info-value">${escapeHtml(o.identity_profile.purpose)}</span>
          <span class="info-label">goals</span><span class="info-value">${o.goals.map(escapeHtml).join("; ") || "none"}</span>
          <span class="info-label">genome</span><span class="info-value mono">${escapeHtml(o.genome_id.slice(0, 12))}…</span>
        </div>
      </div>

      <div class="detail-section">
        <h3>Cells <span class="count">${cells.length}</span></h3>
        <div class="breakdown">${cellRows}</div>
      </div>

      <div class="detail-section">
        <h3>Proteins <span class="count">${recentProteins.length} recent</span></h3>
        <div class="breakdown">${proteinRows}</div>
      </div>

      <div class="detail-section">
        <h3>Memory <span class="count">${memory.length}</span></h3>
        ${memory.length
          ? `<div class="info-grid">
              <span class="info-label">active</span><span class="info-value">${memory.filter((m) => m.status === "active").length}</span>
              <span class="info-label">pending</span><span class="info-value">${memory.filter((m) => m.status === "pending").length}</span>
              <span class="info-label">deprecated</span><span class="info-value">${memory.filter((m) => m.status === "deprecated").length}</span>
            </div>`
          : `<p class="empty">No memory records</p>`}
      </div>

      ${structReqs.length ? `
      <div class="detail-section warn-section">
        <h3>Structure Requests <span class="count warn">${structReqs.filter((r) => r.status === "open").length} open</span></h3>
        ${structReqs.filter((r) => r.status === "open").map((r) => `
          <div class="req-row">
            <span class="mono">${escapeHtml(r.requested_contract)}</span>
            <span class="muted small">${escapeHtml(r.reason)}</span>
          </div>`).join("")}
      </div>` : ""}

    </div>
  `;
}

// ─── Event stream (right panel) ───────────────────────────────────────────────

function renderEventStream(events) {
  const sorted = [...events].reverse().slice(0, 40);
  $("event-count").textContent = sorted.length;
  $("event-stream").innerHTML = sorted.length
    ? sorted.map((ev) => `
        <div class="event-row">
          <span class="event-type ${eventClass(ev.type)}">${escapeHtml(ev.type)}</span>
          <span class="event-msg">${escapeHtml(ev.message)}</span>
          <span class="event-time">${new Date(ev.created_at).toLocaleTimeString()}</span>
        </div>`)
      .join("")
    : `<p class="empty">No events yet</p>`;
}

// ─── Contracts (bottom left) ──────────────────────────────────────────────────

function renderContracts(contracts) {
  const el = $("contracts-panel");
  if (!contracts.length) { el.innerHTML = `<p class="empty">No contracts registered</p>`; return; }
  el.innerHTML = `<table class="data-table">
    <thead><tr><th>Name</th><th>Status</th><th>Uses</th><th>Actions</th></tr></thead>
    <tbody>${contracts.map((c) => `
      <tr>
        <td class="mono small">${escapeHtml(c.name)}</td>
        <td><span class="badge ${c.status === "active" ? "ok" : "neutral"}">${escapeHtml(c.status)}</span></td>
        <td class="num">${c.usage_count}</td>
        <td class="small muted">${c.allowed_actions.slice(0, 2).map(escapeHtml).join(", ") || "any"}</td>
      </tr>`).join("")}
    </tbody>
  </table>`;
}

// ─── Structure requests (bottom right) ───────────────────────────────────────

function renderRequests(requests) {
  const open = requests.filter((r) => r.status === "open");
  $("open-count").textContent = open.length ? `${open.length} open` : "";
  $("open-count").className = `tag ${open.length ? "warn" : "hidden"}`;
  const el = $("requests-panel");
  if (!requests.length) { el.innerHTML = `<p class="empty">No structure requests</p>`; return; }
  el.innerHTML = requests.slice(0, 10).map((r) => `
    <div class="req-item">
      <span class="mono small">${escapeHtml(r.requested_contract)}</span>
      <span class="badge ${r.status === "open" ? "warn" : r.status === "resolved" ? "ok" : "neutral"}">${escapeHtml(r.status)}</span>
      <span class="muted small">${escapeHtml(r.reason)}</span>
    </div>`).join("");
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function lifecycleDot(state) {
  return { active: "green", hibernated: "yellow", degraded: "orange", terminated: "red" }[state] ?? "grey";
}

function lifecycleBadge(state) {
  return { active: "ok", hibernated: "warn", degraded: "warn", terminated: "error" }[state] ?? "neutral";
}

function healthDot(state) {
  return { alive: "green", stressed: "yellow", degraded: "orange", hibernating: "yellow", self_consuming: "red", dead: "grey" }[state] ?? "grey";
}

function proteinBadge(status) {
  return { approved: "ok", repaired: "warn", generated: "neutral", dropped: "error", blocked: "error" }[status] ?? "neutral";
}

function eventClass(type) {
  return { membrane: "ev-cyan", nucleus: "ev-violet", mitochondria: "ev-amber", ribosome: "ev-emerald", protein: "ev-purple", golgi: "ev-orange", skeleton: "ev-pink", peroxisome: "ev-red", structure_request: "ev-pink" }[type] ?? "ev-grey";
}

function groupBy(arr, fn) {
  return arr.reduce((acc, item) => {
    const key = fn(item);
    (acc[key] = acc[key] || []).push(item);
    return acc;
  }, {});
}

function setPulse(active) {
  $("pulse").className = active ? "pulse active" : "pulse";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

async function api(path, options = {}) {
  const init = { method: options.method || "GET", credentials: "include", headers: {} };
  if (options.body !== undefined) {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(options.body);
  }
  return fetch(path, init);
}

// ─── Init ─────────────────────────────────────────────────────────────────────

void tryAutoLogin();
