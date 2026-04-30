/* ─────────────────────────────────────────────
   matrix_script_variation_panel — panel.js
   Zero dependencies. Vanilla ES2020.
   ───────────────────────────────────────────── */

// ═══════════════════════════════════════════════════════
// DATA  — fallback static projection from Matrix Script packet sample.
//         Live mode (?source=live) fetches the same projection from the
//         read-only debug endpoint and then reuses the render flow below.
// ═══════════════════════════════════════════════════════

const DATA = {
  sourceMode: "fallback static",
  packetVersion: "v1",
  readyState: "draft",
  variation_plan: {
    axis_kind_set: ["categorical", "range", "enum"],
    axes: [
      { axis_id: "tone", kind: "categorical", values: ["formal", "casual", "playful"], is_required: true },
      { axis_id: "audience", kind: "enum", values: ["b2b", "b2c", "internal"], is_required: true },
      { axis_id: "length", kind: "range", values: { min: 30, max: 120, step: 15 }, is_required: false },
    ],
    cells: [
      { cell_id: "cell_001", axis_selections: { tone: "formal", audience: "b2b", length: 60 }, script_slot_ref: "slot_001", notes: "primary derivative for B2B formal tone" },
      { cell_id: "cell_002", axis_selections: { tone: "casual", audience: "b2c", length: 45 }, script_slot_ref: "slot_002" },
    ],
  },
  copy_bundle: {
    slot_kind_set: ["primary", "alternate", "fallback"],
    slots: [
      { slot_id: "slot_001", binds_cell_id: "cell_001", language_scope: { source_language: "en-US", target_language: ["zh-CN", "ja-JP"] }, body_ref: "content://matrix_script/v1/slot_001", length_hint: 60 },
      { slot_id: "slot_002", binds_cell_id: "cell_002", language_scope: { source_language: "en-US", target_language: ["zh-CN"] }, body_ref: "content://matrix_script/v1/slot_002", length_hint: 45 },
    ],
  },
  publish_feedback: {
    reference_line: "hot_follow",
    validator_report_path: "docs/execution/logs/packet_validator_matrix_script_v1.json",
    ready_state: "draft",
    deliverable_profile_ref: "deliverable_profile_matrix_script_v1",
    asset_sink_profile_ref: "asset_sink_profile_matrix_script_v1",
  },
  result_packet_binding: {
    generic_refs: ["g_input", "g_struct", "g_scene", "g_audio", "g_lang", "g_deliv"],
    line_specific_refs: ["matrix_script_variation_matrix", "matrix_script_slot_pack"],
    capability_plan: ["understanding", "variation", "subtitles", "dub", "pack"],
    worker_profile_ref: "worker_profile_matrix_script_v1",
  },
};


// ═══════════════════
// DOM HELPERS
// ═══════════════════

/**
 * Minimal createElement wrapper.
 * el(tag, { className, style:{}, ...attrs }, ...children)
 */
function el(tag, attrs = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "className")                  e.className = v;
    else if (k === "style" && typeof v === "object") Object.assign(e.style, v);
    else                                    e.setAttribute(k, v);
  }
  for (const k of kids) {
    if (k == null) continue;
    e.append(typeof k === "string" ? document.createTextNode(k) : k);
  }
  return e;
}

function pill(text, cls) {
  return el("span", { className: `pill ${cls}` }, text);
}

function fieldLabel(text) {
  return el("div", { className: "field-label" }, text);
}

function normalizePanelData(raw) {
  const payload = raw && raw.panel_data ? raw.panel_data : raw;
  const variation = payload.variation_plan || {};
  const bundle = payload.copy_bundle || {};
  const feedback = payload.publish_feedback || {};
  return {
    ...payload,
    axes: payload.axes || variation.axes || [],
    cells: payload.cells || variation.cells || [],
    slots: payload.slots || bundle.slots || [],
    readyState: payload.readyState || feedback.ready_state || "draft",
    packetVersion: payload.packetVersion || payload.packet_version || "v1",
    sourceMode: payload.sourceMode || payload.source_mode || "fallback static",
    variation_plan: variation,
    copy_bundle: bundle,
    publish_feedback: feedback,
    result_packet_binding: payload.result_packet_binding || {},
  };
}

async function loadPanelData() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("source") !== "live") return normalizePanelData(DATA);
  const response = await fetch("/debug/panels/matrix-script/data", {
    headers: { "Accept": "application/json" },
  });
  if (!response.ok) throw new Error(`live preview fetch failed: ${response.status}`);
  return normalizePanelData(await response.json());
}

/** Inline SVG helper (namespace-aware). */
function svg(viewBox, strokeColor, pathData, cls) {
  const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  s.setAttribute("viewBox", viewBox);
  s.setAttribute("fill", "none");
  s.setAttribute("stroke", strokeColor);
  s.setAttribute("stroke-width", "2");
  s.setAttribute("stroke-linecap", "round");
  s.setAttribute("stroke-linejoin", "round");
  if (cls) s.classList.add(cls);
  s.innerHTML = pathData;
  return s;
}

const icons = {
  chevron: () => svg("0 0 24 24", "currentColor",
    `<polyline points="9 18 15 12 9 6"/>`, "chevron"),

  external: (color) => svg("0 0 24 24", color || "var(--c-text-info)",
    `<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
     <polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>`,
    "ext-icon"),

  warn: () => svg("0 0 24 24", "var(--c-text-danger)",
    `<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
     <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>`,
    "warn-icon"),
};


// ═══════════════════
// AXES TABLE
// ═══════════════════

function renderAxes(axes) {
  const tbody = document.getElementById("axes-body");

  axes.forEach((ax) => {
    const tr = el("tr");

    // axis_id
    const idCode = el("code");
    idCode.textContent = ax.axis_id;
    Object.assign(idCode.style, { fontFamily:"var(--font-mono)", fontSize:"12px", color:"var(--c-text-primary)" });
    tr.appendChild(el("td", {}, idCode));

    // kind badge
    tr.appendChild(el("td", {}, pill(ax.kind, `pill-${ax.kind}`)));

    // values — shape varies by kind
    const valCell = el("td", { className: "col-val-cell" });
    if (ax.kind === "range") {
      const c = el("code");
      c.textContent = `{min:${ax.values.min}, max:${ax.values.max}, step:${ax.values.step}}`;
      Object.assign(c.style, { fontFamily:"var(--font-mono)", fontSize:"11px", color:"var(--c-text-secondary)" });
      valCell.appendChild(c);
    } else {
      const wrap = el("div", { className: "axis-values" });
      ax.values.forEach(v => wrap.appendChild(el("span", { className: "pill-value" }, v)));
      valCell.appendChild(wrap);
    }
    tr.appendChild(valCell);

    // required
    const reqCell = ax.is_required
      ? pill("yes", "pill-req")
      : (() => { const s = el("span"); s.textContent="—"; s.style.cssText="font-size:12px;color:var(--c-text-tertiary)"; return s; })();
    tr.appendChild(el("td", {}, reqCell));

    tbody.appendChild(tr);
  });
}


// ═══════════════════
// SLOT DETAIL
// ═══════════════════

function buildSlotDetail(slot) {
  const wrap = el("div", { className: "slot-detail" });
  wrap.id = `detail-${slot.slot_id}`;

  // row 1 — slot_id · binds_cell_id · length_hint
  const r1 = el("div", { className: "sd-grid3" });

  const f1 = el("div");
  f1.appendChild(fieldLabel("slot_id"));
  const tag = el("code", { className: "mono-tag" }); tag.textContent = slot.slot_id;
  f1.appendChild(tag);

  const f2 = el("div");
  f2.appendChild(fieldLabel("binds_cell_id"));
  const bci = el("code", { className: "mono-muted" }); bci.textContent = slot.binds_cell_id;
  f2.appendChild(bci);

  const f3 = el("div");
  f3.appendChild(fieldLabel("length_hint"));
  const lh = el("span", { className: "mono-plain" }); lh.textContent = `${slot.length_hint}s`;
  f3.appendChild(lh);

  r1.append(f1, f2, f3);

  // row 2 — language_scope · body_ref
  const r2 = el("div", { className: "sd-grid2" });

  const fl = el("div");
  fl.appendChild(fieldLabel("language_scope"));
  const lr = el("div", { className: "lang-row" });
  lr.appendChild(pill(slot.language_scope.source_language, "pill-source"));
  const sep = el("span", { className: "lang-sep" }); sep.textContent = "→"; lr.appendChild(sep);
  slot.language_scope.target_language.forEach(t => lr.appendChild(pill(t, "pill-target")));
  fl.appendChild(lr);

  const fb = el("div");
  fb.appendChild(fieldLabel("body_ref"));
  const brc = el("code", { className: "body-ref-code" }); brc.textContent = slot.body_ref;
  fb.appendChild(el("div", { className: "body-ref-wrap" }, brc));

  r2.append(fl, fb);
  wrap.append(r1, r2);
  return wrap;
}


// ═══════════════════
// CELLS TABLE
// ═══════════════════

function renderCells(cells, slots) {
  const container = document.getElementById("cells-body");
  const slotMap   = new Map(slots.map(s => [s.slot_id, s]));

  cells.forEach((cell, i) => {
    const slot    = slotMap.get(cell.script_slot_ref);
    const missing = !slot;
    const isLast  = i === cells.length - 1;

    // ── Row ──
    const row = el("div", { className: "cell-row", role:"row", tabindex:"0",
      "aria-expanded":"false", "aria-controls":`detail-${cell.script_slot_ref}` });
    if (isLast) row.style.borderBottom = "none";

    // cell_id column
    const idWrap = el("div", { className: "cell-id-wrap col-cellid" });
    const chev   = icons.chevron();
    const idCode = el("code"); idCode.textContent = cell.cell_id;
    Object.assign(idCode.style, { fontFamily:"var(--font-mono)", fontSize:"12px", color:"var(--c-text-primary)" });
    idWrap.append(chev, idCode);

    // axis selections column
    const selWrap = el("div", { className: "cell-axes col-axes" });
    for (const [k, v] of Object.entries(cell.axis_selections)) {
      const tok = el("span", { className: "sel-token" });
      const ks  = el("span", { className: "sel-key" }); ks.textContent = k;
      const eq  = el("span", { className: "sel-eq"  }); eq.textContent = "=";
      const vs  = el("span", { className: "sel-val" }); vs.textContent = v;
      tok.append(ks, eq, vs);
      selWrap.appendChild(tok);
    }

    // script_slot ref column
    const slotCol  = el("div", { className: "col-slot" });
    const refRow   = el("div", { className: "slot-ref-wrap" });
    const refCode  = el("code", { className: `slot-ref-code${missing ? " missing" : ""}` });
    refCode.textContent = cell.script_slot_ref;
    refRow.append(refCode, icons.external(missing ? "var(--c-text-danger)" : "var(--c-text-info)"));
    slotCol.appendChild(refRow);

    if (missing) {
      const wr = el("div", { className: "warn-row" });
      const wl = el("span", { className: "warn-label" }); wl.textContent = "unresolved";
      wr.append(icons.warn(), wl);
      slotCol.appendChild(wr);
    }

    // notes column
    const notesCol = el("div", { className: "cell-notes col-notes" });
    notesCol.textContent = cell.notes || "—";

    row.append(idWrap, selWrap, slotCol, notesCol);

    // ── Slot detail (built once, toggled via CSS class) ──
    const detail = slot ? buildSlotDetail(slot) : null;

    // ── Toggle handler ──
    const toggle = () => {
      const open = row.classList.toggle("open");
      chev.classList.toggle("open", open);
      row.setAttribute("aria-expanded", String(open));
      if (detail) detail.classList.toggle("open", open);
    };
    row.addEventListener("click", toggle);
    row.addEventListener("keydown", e => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); }
    });

    container.appendChild(row);
    if (detail) container.appendChild(detail);
  });
}

function renderAttributionTags(data) {
  const container = document.getElementById("attribution-tags");
  const binding = data.result_packet_binding || {};
  const tags = [
    ...(binding.generic_refs || []),
    ...(binding.line_specific_refs || []),
    ...((binding.capability_plan || []).map(kind => `capability:${kind}`)),
    binding.worker_profile_ref ? `worker:${binding.worker_profile_ref}` : null,
  ].filter(Boolean);

  tags.forEach(tag => container.appendChild(el("span", { className: "pill-value" }, tag)));
}

function renderPublishFeedback(data) {
  const feedback = data.publish_feedback || {};
  document.getElementById("source-tag").textContent = data.sourceMode;
  document.getElementById("reference-line").textContent = feedback.reference_line || "";
  document.getElementById("validator-report-path").textContent = feedback.validator_report_path || "";
  document.getElementById("deliverable-profile-ref").textContent = feedback.deliverable_profile_ref || "";
  document.getElementById("asset-sink-profile-ref").textContent = feedback.asset_sink_profile_ref || "";
}


// ═══════════════════
// INIT
// ═══════════════════

document.addEventListener("DOMContentLoaded", async () => {
  let panelData;
  try {
    panelData = await loadPanelData();
  } catch (error) {
    console.warn("[matrix-script-panel] live data unavailable; using fallback", error);
    panelData = normalizePanelData(DATA);
  }
  const { axes, cells, slots, readyState, packetVersion } = panelData;

  // ready_state badge
  const badge = document.getElementById("ready-badge");
  badge.textContent = readyState;
  badge.className   = `pill pill-${readyState}`;

  // packet version
  document.querySelector(".packet-ver").textContent = `packet ${packetVersion}`;

  renderAxes(axes);
  renderCells(cells, slots);
  renderAttributionTags(panelData);
  renderPublishFeedback(panelData);

  // footer summary
  document.getElementById("footer-count").textContent =
    `${axes.length} axes · ${cells.length} cells · ${slots.length} slots`;
});
