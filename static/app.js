// Sylvan Eye page logic, step 4: the form and the wait. Step 5 draws the real results.
"use strict";

// Your test sites (from HANDOFF.md). Edit this list to add more.
var SITES = [
  { name: "Bilaspur city centre", lat: 22.0797, lon: 82.1409 },
  { name: "Fadhakhar Park", lat: 22.042991, lon: 82.173492 },
  { name: "Khapri (farmland)", lat: 22.033592, lon: 82.265111 },
  { name: "Ash dyke", lat: 22.07937, lon: 82.281826 },
  { name: "Green farmland (checked on map)", lat: 22.002166, lon: 82.195423 }
];

var POLL_MS = 2000;       // how often to ask the server for the job status
var SLOW_HINT_AFTER_S = 8;
var MAX_FAILED_POLLS = 3; // consecutive network failures before giving up

var MAX_LLM_WAIT_S = 1200; // stop waiting for the local model after 20 minutes

function $(id) { return document.getElementById(id); }

// Local language models the server offers (step 6). Empty means the controls are not drawn.
var LLM = { models: [], defaultModel: "", analysisId: null };

// ---------------------------------------------------------------- input helpers
// "22.0797, 82.1409" or "22.0797 82.1409" -> {lat, lon}, otherwise null.
function parsePasted(text) {
  var m = /^\s*(-?\d+(?:\.\d+)?)\s*[, ]\s*(-?\d+(?:\.\d+)?)\s*$/.exec(text);
  return m ? { lat: parseFloat(m[1]), lon: parseFloat(m[2]) } : null;
}

// Empty or non-numeric text -> null (Number("") would be 0, which is a real latitude).
function toNumber(text) {
  var t = text.trim();
  if (t === "" || isNaN(Number(t))) { return null; }
  return Number(t);
}

function setPoint(lat, lon) {
  $("lat").value = String(lat);
  $("lon").value = String(lon);
}

function showFormError(msg) {
  var el = $("form-error");
  el.textContent = msg;
  el.hidden = (msg === "");
}

// ---------------------------------------------------------------- form wiring
function fillSiteMenu() {
  var sel = $("site");
  var blank = document.createElement("option");
  blank.value = "";
  blank.textContent = "Choose a site...";
  sel.appendChild(blank);
  SITES.forEach(function (s, i) {
    var o = document.createElement("option");
    o.value = String(i);
    o.textContent = s.name;
    sel.appendChild(o);
  });
}

$("paste").addEventListener("input", function () {
  var text = $("paste").value;
  if (text.trim() === "") { $("paste-msg").textContent = ""; return; }
  var p = parsePasted(text);
  if (p) {
    setPoint(p.lat, p.lon);
    $("site").value = "";
    $("paste-msg").textContent = "Read as " + p.lat + ", " + p.lon;
  } else {
    $("paste-msg").textContent = "Could not read that. Expected two numbers like 22.0797, 82.1409";
  }
});

$("site").addEventListener("change", function () {
  if ($("site").value === "") { return; }
  var s = SITES[Number($("site").value)];
  setPoint(s.lat, s.lon);
  $("paste").value = "";
  $("paste-msg").textContent = "";
});

// ---------------------------------------------------------------- running a job
var currentRun = 0;   // each Analyse click gets a new number; old polling loops see they are stale

$("analyze-form").addEventListener("submit", function (event) {
  event.preventDefault();
  showFormError("");

  var demo = $("demo").checked;
  var lat = toNumber($("lat").value);
  var lon = toNumber($("lon").value);
  var radius = toNumber($("radius").value);

  if (!demo) {
    if (lat === null || lat < -90 || lat > 90) { return showFormError("Latitude must be a number between -90 and 90."); }
    if (lon === null || lon < -180 || lon > 180) { return showFormError("Longitude must be a number between -180 and 180."); }
  }
  if (radius === null || radius <= 0) { return showFormError("Radius must be a number above 0."); }

  startRun({
    lat: lat === null ? 0 : lat,      // the server still needs numbers in demo mode
    lon: lon === null ? 0 : lon,
    radius_m: radius,
    refresh: $("refresh").checked,
    demo: demo
  });
});

function startRun(body) {
  var run = ++currentRun;
  var startedAt = Date.now();

  $("go").disabled = true;
  $("results").hidden = true;
  $("results").textContent = "";
  $("slow-hint").hidden = true;
  $("status-box").hidden = false;
  setStatus("Sending request...", 0);

  fetch("/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  })
    .then(function (r) {
      if (r.status === 422) { throw new Error("The server rejected those values (check the coordinates and radius)."); }
      if (!r.ok) { throw new Error("The server answered " + r.status + "."); }
      return r.json();
    })
    .then(function (data) { poll(data.job_id, run, startedAt, 0); })
    .catch(function (err) { fail(run, err.message); });
}

// One poll, then schedule the next one only after this one has finished. (A fixed
// setInterval could start a second request before the first returned on a slow connection.)
function poll(jobId, run, startedAt, failedInARow) {
  if (run !== currentRun) { return; }          // the user started a newer run

  fetch("/jobs/" + jobId)
    .then(function (r) {
      if (!r.ok) { throw new Error("status " + r.status); }
      return r.json();
    })
    .then(function (job) {
      if (run !== currentRun) { return; }
      var secs = (Date.now() - startedAt) / 1000;
      if (job.state === "done") { return finish(run, job, secs); }
      if (job.state === "error") { return fail(run, "The analysis failed: " + job.error); }
      setStatus(job.stage, secs);
      setTimeout(function () { poll(jobId, run, startedAt, 0); }, POLL_MS);
    })
    .catch(function () {
      if (run !== currentRun) { return; }
      if (failedInARow + 1 >= MAX_FAILED_POLLS) {
        return fail(run, "Lost contact with the server. Is it still running?");
      }
      setTimeout(function () { poll(jobId, run, startedAt, failedInARow + 1); }, POLL_MS);
    });
}

function setStatus(stage, seconds) {
  $("status").textContent = stage + " (" + Math.round(seconds) + " s)";
  $("slow-hint").hidden = seconds < SLOW_HINT_AFTER_S;
}

function fail(run, message) {
  if (run !== currentRun) { return; }
  $("go").disabled = false;
  $("status-box").hidden = true;
  showFormError(message);
}

// ---------------------------------------------------------------- results (step 5)
// Everything the server sends goes in with textContent, never innerHTML.
function el(tag, className, text) {
  var e = document.createElement(tag);
  if (className) { e.className = className; }
  if (text !== undefined) { e.textContent = text; }
  return e;
}

var VERDICT_WORDS = { good: "good", within_limits: "within limits", marginal: "marginal",
                      poor: "poor", skipped: "no data", ok: "ok" };
var VERDICT_CLASS = { good: "chip-ok", within_limits: "chip-ok", ok: "chip-ok",
                      marginal: "chip-marginal", poor: "chip-poor", skipped: "chip-nodata" };
var FACTOR_LABELS = { rainfall: "Rainfall", temperature: "Temperature", pH: "pH",
                      texture: "Texture", elevation: "Elevation" };
var ENV_LABELS = [["annual_rainfall_mm", "Rainfall (mm a year)"],
                  ["annual_mean_temp_c", "Mean temperature (C)"],
                  ["ph", "Soil pH"], ["soil_texture", "Soil texture"],
                  ["elevation_m", "Elevation (m)"]];

function renderResults(r) {
  var root = $("results");
  root.textContent = "";
  root.appendChild(renderBanner(r));
  if (r.facts.warnings.length > 0) { root.appendChild(renderWarnings(r.facts.warnings)); }
  root.appendChild(renderConditions(r.facts.environment));
  root.appendChild(renderPlants(r));
  root.appendChild(renderLimits(r));
  root.appendChild(renderRuledOut(r.facts));
  root.appendChild(renderPlain(r));

  var raw = el("details", "raw");
  raw.appendChild(el("summary", "", "Raw result (for checking)"));
  raw.appendChild(el("pre", "", JSON.stringify(r, null, 2)));
  root.appendChild(raw);
  root.hidden = false;
}

function renderBanner(r) {
  var f = r.facts, cls, title, sub;
  if (f.blocked) {
    cls = "banner-blocked";
    title = "BLOCKED: no plants are recommended for this location.";
    sub = "The reason is in the warning below.";
  } else if (r.location.demo) {
    cls = "banner-demo";
    title = "Offline demo values: the terrain checks were not run.";
    sub = "These are saved Bilaspur values, not the coordinates you typed.";
  } else if (f.warnings.length > 0) {
    cls = "banner-warn";
    title = f.warnings.length + (f.warnings.length === 1 ? " warning" : " warnings") + " for this location.";
    sub = "Read them before the plant list.";
  } else {
    cls = "banner-ok";
    title = "No terrain warnings.";
    sub = "The terrain checks found nothing to flag at this radius. What they cannot see is listed under Data limits.";
  }
  var b = el("div", "banner " + cls);
  b.setAttribute("role", "status");
  b.appendChild(el("p", "banner-title", title));
  b.appendChild(el("p", "", sub));
  if (!r.location.demo) {
    b.appendChild(el("p", "banner-loc", "Location " + r.location.lat + ", " + r.location.lon +
                      "  |  radius used: " + r.location.radius_m + " m"));
  }
  return b;
}

function renderWarnings(warnings) {
  var s = el("section", "block");
  s.appendChild(el("h2", "", "Eligibility warnings"));
  var ul = el("ul", "warnings");
  warnings.forEach(function (w) {
    ul.appendChild(el("li", w.indexOf("BLOCKED") === 0 ? "warning warning-blocked" : "warning", w));
  });
  s.appendChild(ul);
  return s;
}

function renderConditions(env) {
  var s = el("section", "block");
  s.appendChild(el("h2", "", "Conditions at this location"));
  var dl = el("dl", "conditions");
  ENV_LABELS.forEach(function (pair) {
    if (env[pair[0]] === undefined) { return; }
    var item = el("div", "cond");
    item.appendChild(el("dt", "", pair[1]));
    item.appendChild(el("dd", "", String(env[pair[0]])));
    dl.appendChild(item);
  });
  s.appendChild(dl);
  return s;
}

function renderPlants(r) {
  var s = el("section", "block");
  s.appendChild(el("h2", "", "Plants"));
  if (r.facts.blocked) {
    s.appendChild(el("p", "", "No plants are recommended for this location."));
    return s;
  }
  s.appendChild(el("p", "hint", "Plants are grouped, not ranked: the data cannot put plants in the same group in order. Open a plant to see the reason for each check."));
  r.tier_order.forEach(function (tier) {
    var plants = r.tiers[tier];
    var group = el("div", "tier tier-" + tier);
    group.appendChild(el("h3", "", r.tier_labels[tier] + " (" + plants.length + ")"));
    group.appendChild(el("p", "hint", r.tier_descriptions[tier]));
    if (plants.length === 0) { group.appendChild(el("p", "none", "None.")); }
    plants.forEach(function (p) { group.appendChild(renderPlant(p)); });
    s.appendChild(group);
  });
  return s;
}

function renderPlant(p) {
  var d = el("details", "plant");
  var sum = el("summary", "");
  sum.appendChild(el("span", "plant-name", p.name));
  sum.appendChild(el("span", "plant-sci", " (" + p.scientific_name + ")"));
  var chips = el("div", "chips");
  Object.keys(p.checks).forEach(function (factor) {
    var c = p.checks[factor];
    var word = VERDICT_WORDS[c.result] || c.result;
    chips.appendChild(el("span", "chip " + (VERDICT_CLASS[c.result] || "chip-nodata"),
                         (FACTOR_LABELS[factor] || factor) + ": " + word));
  });
  p.flags.forEach(function (flag) { chips.appendChild(el("span", "chip chip-flag", "Flag: " + flag)); });
  sum.appendChild(chips);
  d.appendChild(sum);

  var ul = el("ul", "why");
  Object.keys(p.checks).forEach(function (factor) {
    var c = p.checks[factor];
    ul.appendChild(el("li", "", (FACTOR_LABELS[factor] || factor) + ", " +
                      (VERDICT_WORDS[c.result] || c.result) + ": " + c.detail));
  });
  ul.appendChild(el("li", "", "Checks with data: " + p.factors_with_data + ". Tier reason: " + p.tier_reason + "."));
  d.appendChild(ul);
  return d;
}

function renderLimits(r) {
  var s = el("section", "block panel-info");
  s.appendChild(el("h2", "", "Data limits"));
  var ul = el("ul", "");
  r.facts.limits.forEach(function (text) { ul.appendChild(el("li", "", text)); });
  s.appendChild(ul);
  s.appendChild(el("p", "", r.location.demo ? "Radius: not used (offline demo)."
                                             : "Radius used: " + r.location.radius_m + " m. A different radius can change the result."));
  s.appendChild(el("p", "", r.terrain_summary ? r.terrain_summary : "Terrain was not measured."));
  if (r.cache.length > 0) {
    var store = "off", parts = [];
    r.cache.forEach(function (e) { if (e[0] === "store") { store = e[1]; } else { parts.push(e[0] + " " + e[1]); } });
    s.appendChild(el("p", "hint", "Cache (" + store + "): " + parts.join(", ")));
  }
  return s;
}

function renderRuledOut(facts) {
  var s = el("section", "block");
  var out = facts.ruled_out;
  if (out.length === 0) {
    s.appendChild(el("h2", "", "Ruled out (0)"));
    s.appendChild(el("p", "", "No plant was ruled out."));
  } else {
    var d = el("details", "ruled");
    d.appendChild(el("summary", "", "Ruled out (" + out.length + ")"));
    var ul = el("ul", "");
    out.forEach(function (o) {
      var li = el("li", "");
      li.appendChild(el("strong", "", o.name));
      li.appendChild(document.createTextNode(": " + o.reason));
      ul.appendChild(li);
    });
    d.appendChild(ul);
    s.appendChild(d);
  }
  if (facts.not_assessed_no_data.length > 0) {
    s.appendChild(el("p", "hint", "Not assessed, no data in the plant database (" +
                     facts.not_assessed_no_data.length + "): " + facts.not_assessed_no_data.join(", ")));
  }
  return s;
}

function renderPlain(r) {
  var ex = r.explanation;
  var s = el("section", "block");
  s.appendChild(el("h2", "", "In plain words"));
  s.appendChild(el("p", "hint", ex.source === "template"
    ? "Written by fixed rules from the same facts. No LLM was used."
    : "Written by a language model; check it against the sections above."));
  s.appendChild(el("pre", "plain", ex.text));
  if (ex.notes && ex.notes.length > 0) {
    var ul = el("ul", "hint");
    ex.notes.forEach(function (n) { ul.appendChild(el("li", "", n)); });
    s.appendChild(ul);
  }
  s.appendChild(renderLlmControls(r.facts.blocked));
  return s;
}

// ---------------------------------------------------------------- optional language model (step 6)
// The rules result above never waits for this. The model only rephrases the same facts, its
// answer is checked on the server, and its text is always shown separately and labelled.
function renderLlmControls(blocked) {
  var box = el("div", "llm-box");
  if (blocked) {
    box.appendChild(el("p", "hint", "The language model is never used for a blocked location."));
    return box;
  }
  if (LLM.models.length === 0) { return box; }
  box.appendChild(el("h3", "", "Optional: rewrite with a local language model"));
  box.appendChild(el("p", "hint", "Needs Ollama running on this computer. The model only rephrases the facts above, its answer is checked, and the text above stays unchanged for comparison."));

  var row = el("div", "llm-row");
  var sel = el("select", "llm-model");
  sel.setAttribute("aria-label", "Local model");
  LLM.models.forEach(function (m) {
    var o = el("option", "", m);
    o.value = m;
    sel.appendChild(o);
  });
  sel.value = LLM.defaultModel;
  var btn = el("button", "llm-go", "Rewrite with local LLM");
  btn.type = "button";
  row.appendChild(sel);
  row.appendChild(btn);
  box.appendChild(row);

  var status = el("p", "hint llm-status");
  status.setAttribute("aria-live", "polite");
  var out = el("div", "llm-out");
  box.appendChild(status);
  box.appendChild(out);

  btn.addEventListener("click", function () { startLlm(sel.value, btn, status, out); });
  return box;
}

function startLlm(model, btn, status, out) {
  var run = currentRun;
  var startedAt = Date.now();
  btn.disabled = true;
  out.textContent = "";
  status.textContent = "Starting...";

  fetch("/jobs/" + LLM.analysisId + "/explain", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: model })
  })
    .then(function (r) {
      if (r.ok) { return r.json(); }
      return r.json().then(function (b) {
        throw new Error(typeof b.detail === "string" ? b.detail : "the server refused the request");
      });
    })
    .then(function (d) { pollLlm(d.job_id, run, startedAt, 0, btn, status, out); })
    .catch(function (err) { llmFail(run, err.message, btn, status, out); });
}

function pollLlm(jobId, run, startedAt, failedInARow, btn, status, out) {
  if (run !== currentRun) { return; }
  fetch("/jobs/" + jobId)
    .then(function (r) {
      if (!r.ok) { throw new Error("status " + r.status); }
      return r.json();
    })
    .then(function (job) {
      if (run !== currentRun) { return; }
      var secs = (Date.now() - startedAt) / 1000;
      if (job.state === "done") {
        status.textContent = "Done (" + Math.round(secs) + " s)";
        btn.disabled = false;
        renderLlmResult(out, job.result);
        return;
      }
      if (job.state === "error") { return llmFail(run, job.error, btn, status, out); }
      if (secs > MAX_LLM_WAIT_S) { return llmFail(run, "Still no answer after 20 minutes. Check that Ollama is running.", btn, status, out); }
      status.textContent = job.stage + " (" + Math.round(secs) + " s)";
      setTimeout(function () { pollLlm(jobId, run, startedAt, 0, btn, status, out); }, POLL_MS);
    })
    .catch(function () {
      if (run !== currentRun) { return; }
      if (failedInARow + 1 >= MAX_FAILED_POLLS) {
        return llmFail(run, "Lost contact with the server. Is it still running?", btn, status, out);
      }
      setTimeout(function () { pollLlm(jobId, run, startedAt, failedInARow + 1, btn, status, out); }, POLL_MS);
    });
}

function llmFail(run, message, btn, status, out) {
  if (run !== currentRun) { return; }
  btn.disabled = false;
  status.textContent = "";
  out.textContent = "";
  out.appendChild(el("p", "error", "The local model could not be used: " + message +
                     " The text above is unchanged."));
}

function renderLlmResult(out, res) {
  out.textContent = "";
  var panel = el("div", res.source === "llm" ? "llm-panel" : "llm-panel llm-rejected");
  if (res.source === "llm") {
    panel.appendChild(el("h3", "", "LLM-written text (" + res.model + ")"));
  } else {
    panel.appendChild(el("h3", "", "The model's answer was rejected"));
    panel.appendChild(el("p", "", "The checks rejected what the model wrote, so this is the template text again."));
  }
  panel.appendChild(el("pre", "plain", res.text));
  if (res.notes && res.notes.length > 0) {
    var ul = el("ul", "hint");
    res.notes.forEach(function (n) { ul.appendChild(el("li", "", n)); });
    panel.appendChild(ul);
  }
  out.appendChild(panel);
}

function finish(run, job, seconds) {
  $("go").disabled = false;
  $("slow-hint").hidden = true;
  setStatus("Done", seconds);
  LLM.analysisId = job.job_id;
  renderResults(job.result);
  if ($("results").scrollIntoView) { $("results").scrollIntoView({ block: "start" }); }
}

fillSiteMenu();

// The optional LLM controls only appear if the server answers with a model list.
fetch("/llm/models")
  .then(function (r) { return r.json(); })
  .then(function (d) { LLM.models = d.models; LLM.defaultModel = d.default; })
  .catch(function () { LLM.models = []; });