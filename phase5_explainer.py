"""
Sylvan Eye — Phase 5: explanation layer.

The matcher (phase4_matcher.py) DECIDES which plants fit. This layer only EXPLAINS
that decision in plain English. It never chooses, re-ranks, or adds facts.

Three pieces:
  1. build_facts()          packs the matcher's output into one fact sheet.
  2. template_explanation() deterministic plain-English text. No LLM. This is the
                            default output (the LLM plugin is OFF unless you ask).
  3. OllamaExplainer        optional local LLM that rewrites the fact sheet as prose.
                            Its answer is CHECKED before use: any plant or number that
                            is not in the fact sheet makes it get rejected, and the
                            template is used instead.

Run:
    python phase5_explainer.py --demo                 offline demo values, template text
    python phase5_explainer.py --demo --llm           same, but explained by the local LLM
    python phase5_explainer.py LAT LON                live location, template text
    python phase5_explainer.py LAT LON --llm          live location, LLM text
    add  --model qwen2.5:7b-instruct  to pick another Ollama model
    add  --radius 1000  to size the terrain circle in metres (default 400)
"""

import csv
import json
import re
import sys

import requests

from phase4_matcher import DEMO_ENV, PLANTS_CSV, check_eligibility, match_plants, parse_radius, run_live

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "gemma4:e4b"   # change here or pass --model
TOP_N = 8                     # plants shown to the explainer
MAX_RETRIES = 1               # extra attempts after a rejected LLM answer

LIMITS = [
    "Soil pH and texture come from a modelled 250 m dataset, and rainfall and temperature "
    "come from reanalysis data. Confirm with a local soil test before planting.",
    "Plants with equal scores are not ranked against each other; the data cannot separate them.",
]


# ---------------------------------------------------------------------------
# 1. Fact sheet
# ---------------------------------------------------------------------------
def build_facts(env, terrain, ranked, excluded, blank, top=TOP_N):
    blocked, warnings = (False, [])
    if terrain:
        blocked, warnings = check_eligibility(terrain)

    shortlist = []
    if not blocked:
        for e in ranked[:top]:
            shortlist.append({
                "name": e["name"],
                "scientific_name": e["scientific_name"],
                "score": e["score"],
                "factors_with_data": f"{e['confidence_n']} of 5",
                "checks": {k: {"result": v or "skipped", "detail": why}
                           for k, (v, why) in e["factors"].items()},
                "flags": e["flags"],
            })
    return {
        "environment": env,
        "blocked": blocked,
        "warnings": warnings,
        "shortlist": shortlist,
        "shortlist_note": f"showing the top {min(top, len(ranked))} of {len(ranked)} plants not ruled out",
        "ruled_out": [{"name": e["name"], "reason": e["excluded_because"]} for e in excluded],
        "not_assessed_no_data": blank,
        "limits": LIMITS,
    }


# ---------------------------------------------------------------------------
# 2. Template explanation (no LLM)
# ---------------------------------------------------------------------------
def _join(items):
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def template_explanation(facts):
    env = facts["environment"]
    lines = [
        f"Conditions at this location: about {env['annual_rainfall_mm']} mm of rain a year, "
        f"a mean temperature of {env['annual_mean_temp_c']} C, soil pH {env['ph']}, "
        f"{env['soil_texture']} soil texture, at {env['elevation_m']} m elevation."
    ]
    for w in facts["warnings"]:
        lines.append(w)
    if facts["blocked"]:
        lines.append("No plant recommendations are given for this location.")
        return "\n".join(lines)

    lines.append(f"\nPlants that fit ({facts['shortlist_note']}):")
    for p in facts["shortlist"]:
        by = {"good": [], "within_limits": [], "marginal": [], "poor": [], "skipped": []}
        details = {}
        for factor, c in p["checks"].items():
            if factor == "elevation" and c["result"] == "ok":
                continue
            by.setdefault(c["result"], []).append(factor)
            details[factor] = c["detail"]
        parts = []
        if by["good"]:
            parts.append(f"{_join(by['good'])} sit inside its typical range")
        if by["within_limits"]:
            parts.append(f"{_join(by['within_limits'])} are within its stated limits")
        for f in by["marginal"] + by["poor"]:
            parts.append(f"{f} is {p['checks'][f]['result']}: {details[f]}")
        if by["skipped"]:
            parts.append(f"no data to check {_join(by['skipped'])}")
        text = f"- {p['name']} ({p['scientific_name']}): " + "; ".join(parts) + "."
        for flag in p["flags"]:
            text += f" Note: {flag}."
        lines.append(text)

    if facts["ruled_out"]:
        lines.append("\nRuled out:")
        for r in facts["ruled_out"]:
            lines.append(f"- {r['name']}: {r['reason']}")
    if facts["not_assessed_no_data"]:
        lines.append("\nNot assessed (no data): " + _join(facts["not_assessed_no_data"]) + ".")
    lines.append("\nLimits: " + " ".join(facts["limits"]))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 3. LLM plugin (optional) + verification guard
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You explain the output of a rule-based plant suitability checker to a non-expert.
Strict rules:
- Use ONLY the facts in the JSON you are given.
- Do not mention any plant that is not in the JSON. Do not add plants, advice, or numbers.
- Copy numbers exactly as written in the JSON. Do not round, convert, or calculate new numbers.
- Do not decide, re-rank, or change any result. Say "marginal" or "no data" where the JSON says so.
- A check whose result is "skipped" means there is NO DATA. Never describe it as passing, fitting or suitable.
- Use the wording of the flags (for example "able to become a weed"). Do not use other words such as "invasive".
- If "warnings" is not empty, start with them.
- Then explain EVERY plant in "shortlist" in one or two plain sentences, including any caveat or flag.
- For each plant, mention every check whose result is "marginal" or "poor", and every "skipped" check as no data.
- Only say there is no data for a check if its result is "skipped".
- Then name EVERY plant in "ruled_out" with its reason, and every plant in "not_assessed_no_data".
- End with the "limits".
Plain text only: no bold, no headings, no tables. Short paragraphs or dash lists are fine. Finish the whole answer."""


class OllamaExplainer:
    """Local LLM through Ollama. Swap this class for any other provider with the same method."""

    def __init__(self, model=OLLAMA_MODEL, url=OLLAMA_URL):
        self.model, self.url = model, url
        self.name = f"ollama:{model}"

    def explain(self, system, user):
        payload = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": 0.1, "num_ctx": 8192, "num_predict": 2048},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        try:
            resp = requests.post(self.url, json=payload, timeout=300)
            resp.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise RuntimeError("Could not reach Ollama. Start it (ollama serve) and check the model "
                               f"is pulled (ollama pull {self.model}).")
        data = resp.json()
        self.truncated = data.get("done_reason") == "length"   # model hit a length limit mid-answer
        text = data.get("message", {}).get("content", "")
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
        return text.replace("**", "").strip()


NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def _numbers(text):
    return [float(n) for n in NUMBER.findall(text)]


def _plant_vocabulary(plants_csv=PLANTS_CSV):
    """Every plant name in plants.csv, split on ' / ' so aliases count too."""
    names = set()
    with open(plants_csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for field in ("common_name", "scientific_name"):
                for part in (row.get(field) or "").split("/"):
                    part = part.strip().lower()
                    if part:
                        names.add(part)
    return names


FACTOR_WORDS = {
    "rainfall": [r"rainfall", r"\brain\b"],
    "temperature": [r"temperature"],
    "pH": [r"\bph\b"],
    "texture": [r"texture"],
    "elevation": [r"elevation", r"altitude"],
}
NO_DATA = re.compile(
    r"\bno\b.{0,15}\b(data|information)\b|\black\w*|\bmissing\b|not available|unavailable|without data|"
    r"not assessed|not checked|could not be checked|skipped|not provided|\bexcept\b[^.;]{0,60}\bdata\b",
    re.I,
)
# Words a small model tends to add from its own background knowledge. If one appears in the
# explanation but not in the fact sheet, the answer is rejected.
UNSOURCED_TERMS = ["invasive", "endangered", "native", "toxic", "poisonous", "edible", "medicinal",
                   "nitrogen", "timber", "fruit", "shade", "wildlife"]


def _aliases(name):
    """'Bamboo (male bamboo)' -> {'bamboo'}; 'Salai / Indian frankincense' -> {'salai', 'indian frankincense'}"""
    names = set()
    for part in re.sub(r"\(.*?\)", "", name).split("/"):
        part = part.strip().lower()
        if part:
            names.add(part)
    return names


def _plant_names(entry):
    return _aliases(entry["name"]) | _aliases(entry["scientific_name"])


def _mentions(factor, text):
    return any(re.search(pattern, text) for pattern in FACTOR_WORDS[factor])


def _segments(text, shortlist):
    """Split the explanation into one piece per shortlisted plant (from its first mention
    to the next plant's mention or the next blank line)."""
    lowered = text.lower()
    starts = []
    for entry in shortlist:
        positions = [m.start() for n in _plant_names(entry)
                     for m in re.finditer(rf"\b{re.escape(n)}\b", lowered)]
        if positions:
            starts.append((min(positions), entry))
    starts.sort(key=lambda item: item[0])
    pieces = []
    for i, (pos, entry) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        blank = text.find("\n\n", pos)
        if blank != -1:
            end = min(end, blank)
        pieces.append((entry, text[pos:end]))
    return pieces


def _per_plant_problems(text, facts):
    """
    For each shortlisted plant's piece of text:
      A. talking about a factor that was SKIPPED without saying there was no data
      B. saying there was no data for a factor that WAS checked
      C. leaving out a marginal or poor check
    """
    problems = []
    for entry, segment in _segments(text, facts["shortlist"]):
        name, checks, seg = entry["name"], entry["checks"], segment.lower()
        for clause in [c for c in re.split(r"[.!?;]\s+|\n", seg) if c.strip()]:
            matches = list(NO_DATA.finditer(clause))
            if not matches:
                for factor, c in checks.items():
                    if c["result"] == "skipped" and _mentions(factor, clause):
                        problems.append(f"says something about {factor} for {name}, "
                                        f"but there was no data for that check")
            for m in matches:
                window = clause[max(0, m.start() - 14): m.end() + 30]
                for factor, c in checks.items():
                    if c["result"] != "skipped" and _mentions(factor, window):
                        problems.append(f"says {factor} had no data for {name}, "
                                        f"but it was checked ({c['result']})")
        for factor, c in checks.items():
            if c["result"] in ("marginal", "poor") and not _mentions(factor, seg):
                problems.append(f"does not mention the {c['result']} {factor} check for {name}")
    return problems


def _completeness_problems(text, facts):
    """Every shortlisted, ruled-out and no-data plant must be named (catches cut-off or lazy answers)."""
    lowered = text.lower()
    wanted = [(e["name"], _plant_names(e)) for e in facts["shortlist"]]
    wanted += [(r["name"], _aliases(r["name"])) for r in facts["ruled_out"]]
    wanted += [(n, _aliases(n)) for n in facts["not_assessed_no_data"]]
    return [f"leaves out {name}" for name, aliases in wanted
            if not any(re.search(rf"\b{re.escape(a)}\b", lowered) for a in aliases)]


def verify_explanation(text, facts, plants_csv=PLANTS_CSV):
    """
    Returns a list of problems (empty = accepted). Checks:
      - every number with a decimal point or 2+ digits appears SOMEWHERE in the fact sheet
        (single digits like 'one of 5' are ignored). This catches invented numbers, but it
        cannot tell whether a real number is attached to the right claim.
      - no plant from plants.csv is mentioned unless it is in the fact sheet
      - no unsourced background-knowledge words (see UNSOURCED_TERMS)
      - per-plant claims match the checks: no talk about skipped factors, no 'no data' for checked
        factors, no dropped marginal/poor checks (see _per_plant_problems)
      - every shortlisted, ruled-out and no-data plant is named (see _completeness_problems)
    """
    problems = []
    facts_text = json.dumps(facts)
    allowed = _numbers(facts_text)
    for n in _numbers(text):
        if abs(n) < 10 and float(n).is_integer():
            continue
        if not any(abs(n - a) < 0.051 for a in allowed):
            problems.append(f"number {n:g} is not in the fact sheet")

    in_facts = facts_text.lower()
    lowered = text.lower()
    for name in _plant_vocabulary(plants_csv):
        if re.search(rf"\b{re.escape(name)}\b", lowered) and name not in in_facts:
            problems.append(f"mentions '{name}', which is not in the fact sheet")
    facts_lower = json.dumps(facts).lower()
    for term in UNSOURCED_TERMS:
        if re.search(rf"\b{term}", lowered) and term not in facts_lower:
            problems.append(f"uses '{term}', which is not in the fact sheet")

    problems += _per_plant_problems(text, facts)
    problems += _completeness_problems(text, facts)
    return sorted(set(problems))


def explain(facts, explainer=None):
    """
    Returns (text, notes). With no explainer, or when blocked, uses the template.
    With an explainer, the answer must pass verify_explanation or the template is used.
    """
    if explainer is None or facts["blocked"]:
        return template_explanation(facts), []

    user = "Fact sheet:\n" + json.dumps(facts, separators=(",", ":"))
    notes = []
    for attempt in range(1 + MAX_RETRIES):
        text = explainer.explain(SYSTEM_PROMPT, user)
        problems = verify_explanation(text, facts)
        if getattr(explainer, "truncated", False):
            problems.append("the answer was cut off at the model's length limit")
        if not problems:
            return text, notes + [f"LLM-written text ({explainer.name}). Every plant and number was found in the "
                                 f"fact sheet, but a real number can still sit on the wrong claim, so compare it with the plain report"]
        notes.append(f"attempt {attempt + 1} rejected: " + "; ".join(problems))
        user += ("\n\nYour previous answer was rejected because: " + "; ".join(problems) +
                 ". Rewrite it using only the fact sheet.")
    notes.append("LLM answer rejected, showing the deterministic text instead")
    return template_explanation(facts), notes


# ---------------------------------------------------------------------------
def main():
    argv = sys.argv[1:]
    model = OLLAMA_MODEL
    if "--model" in argv:
        i = argv.index("--model")
        model = argv[i + 1]
        del argv[i:i + 2]
    radius = parse_radius(argv)
    use_llm = "--llm" in argv
    args = [a for a in argv if not a.startswith("--")]

    if "--demo" in argv:
        env, terrain = dict(DEMO_ENV), None
        print("Location: demo values measured for Bilaspur (offline)\n")
    else:
        lat, lon = (float(args[0]), float(args[1])) if len(args) >= 2 else (22.0797, 82.1409)
        print(f"Location: {lat}, {lon} (terrain radius {radius:g} m)\n")
        env, terrain = run_live(lat, lon, radius)

    ranked, excluded, blank = match_plants(env)
    facts = build_facts(env, terrain, ranked, excluded, blank)
    text, notes = explain(facts, OllamaExplainer(model) if use_llm else None)

    print(text)
    for n in notes:
        print(f"\n[{n}]")


if __name__ == "__main__":
    main()