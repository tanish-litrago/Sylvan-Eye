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

function $(id) { return document.getElementById(id); }

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

// Step 4 placeholder: prove the result arrived. Step 5 replaces this with the real page.
function finish(run, job, seconds) {
  $("go").disabled = false;
  $("slow-hint").hidden = true;
  setStatus("Done", seconds);

  var r = job.result;
  var counts = r.tier_order.map(function (t) { return r.tier_labels[t] + ": " + r.tiers[t].length; });
  var blocked = r.facts.blocked ? "BLOCKED. " : "";
  var summary = document.createElement("p");
  summary.textContent = blocked + counts.join(", ") + ". Ruled out: " + r.facts.ruled_out.length +
    ". Warnings: " + r.facts.warnings.length + ". Radius used: " + r.location.radius_m + " m.";

  var raw = document.createElement("details");
  var label = document.createElement("summary");
  label.textContent = "Raw result (for checking)";
  var pre = document.createElement("pre");
  pre.textContent = JSON.stringify(r, null, 2);
  raw.appendChild(label);
  raw.appendChild(pre);

  $("results").textContent = "";
  $("results").appendChild(summary);
  $("results").appendChild(raw);
  $("results").hidden = false;
}

fillSiteMenu();
