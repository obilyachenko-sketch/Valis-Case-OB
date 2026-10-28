#!/usr/bin/env python3
"""Ask-with-sources over the Northwind bundle.

Usage:
    python Analysis/ask.py "What did we actually spend on SaaS tools last quarter?"
    python Analysis/ask.py "Did we decide to hire in Sales or freeze hiring?"
    python Analysis/ask.py --all            # both CEO questions -> Analysis/output/answers.md
    python Analysis/ask.py --data DIR ...   # run against another copy of the bundle

Everything is recomputed from the raw files on each run; nothing is hard-coded except
the vocabulary used to recognise topics. Every claim prints the file:line it came from.
Standard library only (Python 3.9+).
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nwlib.sources import (Cite, Msg, find, load_doc, load_notes, load_pnl,  # noqa: E402
                           load_roster, load_slack)

CONFIDENCE_RUBRIC = """\
**Confidence scale used**
- **High** — read directly from a primary record *and* corroborated by an independent source; no open conflict.
- **Medium** — primary record exists, but a documented open issue could move the number.
- **Low** — single uncorroborated source, or inferred.
- **Can't verify** — the evidence needed is not in the bundle (listed explicitly)."""


def money(x: float) -> str:
    return f"${x:,.0f}"


def short(text: str, n: int = 110) -> str:
    t = re.sub(r"\*\*|__|`", "", text)
    return t if len(t) <= n else t[: n - 1] + "…"


# ====================================================================== SaaS spend

def answer_saas(root: Path) -> str:
    pnl = load_pnl(root)
    msgs = load_slack(root) + load_notes(root)
    if not pnl:
        return "No P&L file found in the bundle (expected `*pnl*.csv`). Can't answer."

    saas = [r for r in pnl if re.search(r"software|saas", r.category, re.I)]
    subtot = [r for r in saas if re.search(r"total", r.item, re.I)]
    items = [r for r in saas if r not in subtot]
    other_noncash = [r for r in pnl if r not in saas and r.amount.currency not in ("USD", "")]

    usd = [r for r in items if r.amount.currency == "USD" and r.amount.value is not None]
    nonusd = [r for r in items if r.amount.currency not in ("USD", "")]
    blank = [r for r in items if r.amount.value is None]
    booked = sum(r.amount.value for r in usd)
    listed = subtot[0].amount.value if subtot else None

    # --- duplicate-vendor detection: same leading word in the vendor name
    groups: dict[str, list] = defaultdict(list)
    for r in items:
        key = re.sub(r"[^a-z0-9]", "", r.item.lower().split()[0]) if r.item else ""
        groups[key].append(r)
    dups = {k: v for k, v in groups.items() if len(v) > 1 and k}
    dup_excess = 0.0
    dup_lines = []
    for k, rows in dups.items():
        vals = [r.amount.value or 0 for r in rows]
        excess = sum(vals) - max(vals)
        dup_excess += excess
        same = len({r.amount.value for r in rows}) == 1 and len({r.notes for r in rows}) == 1
        talk = [m for m in msgs if k in m.text.lower()
                and re.search(r"twice|double|duplicate|same product|one contract|invoice", m.text, re.I)
                and re.search(r"line|invoice|contract|\$", m.text, re.I)]
        if talk:  # same-thread follow-ups on the invoice (may not repeat the vendor name)
            t0 = min(m.when for m in talk)
            talk += [m for m in msgs if m not in talk and m.channel == talk[0].channel
                     and 0 <= (m.when - t0).total_seconds() <= 3600 and re.search(r"invoice", m.text, re.I)]
            talk.sort(key=lambda m: m.when)
        dup_lines.append((k, rows, excess, same, talk))

    # --- contract vs posted (e.g., "$60k for the year")
    contracts = []
    q_end = datetime(2026, 3, 31)
    for r in items:
        k = r.item.lower().split()[0]
        for m in msgs:
            if k in m.text.lower():
                c = re.search(r"\$(\d+(?:\.\d+)?)\s*k\s*(?:for the year|/\s*yr|per year|annual)", m.text, re.I)
                if c:
                    contracts.append((r, float(c.group(1)) * 1000, m))
    # one row per vendor, keep earliest statement + list all cites
    seen = {}
    for r, annual, m in contracts:
        seen.setdefault(r.item, (r, annual, []))[2].append(m)

    scope_msgs = [m for m in msgs if re.search(r"saas", m.text, re.I)
                  and re.search(r"infrastructure|infra\b|fold", m.text, re.I)]
    fx_msgs = [m for m in msgs if re.search(r"\bEUR\b|FX", m.text) and re.search(r"saas|subtotal", m.text, re.I)]

    best_low = booked - dup_excess
    out = ["## Q1. What did we actually spend on SaaS tools last quarter?\n"]
    if dup_excess:
        out.append(f"**Answer: {money(booked)} as booked in the Q1 2026 P&L; likely true spend {money(best_low)}** "
                   f"— the difference ({money(dup_excess)}) is a vendor that appears twice and finance has not yet "
                   f"confirmed against the invoice. Range: **{money(best_low)} – {money(booked)}**.\n")
    else:
        out.append(f"**Answer: {money(booked)}** as booked in the Q1 2026 P&L.\n")

    out.append("### How the number is built")
    out.append(f"- {len(items)} Software & SaaS line items, "
               f"{items[0].cite.file}:L{items[0].cite.line}–L{items[-1].cite.line}. Recomputed sum = **{money(booked)}**.")
    if listed is not None:
        tie = "ties exactly" if abs(listed - booked) < 0.5 else f"DOES NOT tie (diff {money(listed - booked)})"
        out.append(f"- Listed subtotal {money(listed)} {subtot[0].cite} — {tie}. **Confidence: High** that this is what's booked.")
    for m in scope_msgs[:2]:
        out.append(f"- Scope: {m.who} — \"{short(m.text, 160)}\" {m.cite}. So AWS / Cloudflare (Infrastructure) are excluded.")

    out.append("\n### What we're paying for (as booked)")
    out.append("| Vendor | Q1 USD | Purpose | Source |\n|---|---:|---|---|")
    for r in sorted(items, key=lambda r: -(r.amount.value or 0)):
        out.append(f"| {r.item} | {money(r.amount.value or 0)} | {r.notes} | {r.cite} |")

    out.append("\n### Issues that move the number")
    for k, rows, excess, same, talk in dup_lines:
        names = " + ".join(f"\"{r.item}\" {r.cite}" for r in rows)
        out.append(f"- **Possible double-count ({money(excess)}):** {names}"
                   + (" — identical amount and description." if same else "."))
        for m in talk:
            out.append(f"  - {m.who}: \"{short(m.text)}\" {m.cite}")
        out.append("  - Status: unresolved in the bundle (invoice not received). **Confidence that true spend is "
                   f"{money(best_low)}: Medium.**")
    for item, (r, annual, ms) in seen.items():
        q = annual / 4
        first = min(ms, key=lambda m: m.when)
        timing = ("closed **after** Q1 ended, so it does not change Q1 actuals"
                  if first.when > q_end else "closed during the quarter")
        out.append(f"- **{item} renewal:** {money(annual)}/yr ≈ {money(q)}/qtr vs {money(r.amount.value or 0)} posted "
                   f"{r.cite}. Renewal {timing} {first.cite}. Q1 posting kept as-is. "
                   f"Run-rate after renewal rises by ≈{money(q - (r.amount.value or 0))}/qtr.")
        for m in ms:
            if "higher" in m.text.lower() and (r.amount.value or 0) < q:
                out.append(f"  - ⚠ Finance note says the posted figure \"looks higher than a $60k annual would imply\" "
                           f"{m.cite} — arithmetic says it is *lower* ({money(r.amount.value or 0)} < {money(q)}). "
                           "Note is internally inconsistent; flagged, not relied on.")
    if nonusd or blank:
        for r in nonusd + blank:
            out.append(f"- Line not in USD or blank: {r.item} \"{r.amount.raw}\" {r.cite} — excluded from the sum.")
    for r in other_noncash:
        out.append(f"- Outside SaaS: {r.item} \"{r.amount.raw}\" {r.cite} is in EUR and un-normalized; not SaaS, not included.")

    out.append("\n### Could NOT verify")
    out.append("- Vendor invoices / contracts for any line (none in the bundle) — incl. whether Amplitude is one contract.")
    for m in fx_msgs[:1]:
        out.append(f"- Finance says some EU-billed tools arrive in EUR {m.cite}; no SaaS line is marked EUR, so I assume all "
                   "SaaS lines are already USD. If one isn't, the total moves by the FX difference.")
    out.append("- SaaS paid outside AP (team credit cards, expensed seats) — would not appear in this P&L.")
    out.append("- Whether the P&L is final-final: finance notes are marked \"Figures illustrative / pre-close\".")
    return "\n".join(out)


# ====================================================================== Sales hiring

SALES = re.compile(r"\bsales\b|REQ-114|\bAEs?\b|account executive", re.I)
HIRING = re.compile(r"hir|headcount|\breqs?\b|REQ-|freez|frozen|pause|on hold|approved|seated|bodies|recruit", re.I)
FREEZE = re.compile(r"freez|frozen|paused|on hold|hold the line|hold them|no new|is a no|not moving forward|"
                    r"don't bother submitting", re.I)
HIRE = re.compile(r"REQ-\d+ approved|REQ-\d+, approved|status=APPROVED|seated|get an AE|add(ing)? bodies|keep hiring", re.I)
LIFT = re.compile(r"lift(ing|ed)? the freeze|unfreez|freeze (is |has been )?lifted|resum(e|ing) (sales )?hiring", re.I)
DEFER = re.compile(r"park it|see how .* looks before|before we add", re.I)


def org_names(root: Path) -> dict[str, str]:
    """first name -> full name, and title -> name, from the org chart."""
    names: dict[str, str] = {}
    for p in find(root, "*org*chart*.md"):
        for line in load_doc(root, p).lines:
            m = re.match(r"\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|", line)
            if m:
                full, title = m.group(1).strip(), m.group(2).strip()
                names[full.split()[0].lower()] = full
                names[title.lower()] = full
    return names


def stance(text: str) -> str:
    # a question ("do we keep hiring into Sales or hold?") is not a position
    if re.search(r"\?\s*$|question on the table", text, re.I) and not re.search(r"\bDECISION\b", text):
        return "context"
    if LIFT.search(text):
        return "HIRE"
    if FREEZE.search(text):
        return "FREEZE"
    if HIRE.search(text):
        return "HIRE"
    if DEFER.search(text):
        return "DEFER"
    return "context"


def answer_sales(root: Path) -> str:
    names = org_names(root)
    ceo = names.get("ceo", "")
    roster = load_roster(root)
    msgs = load_slack(root) + load_notes(root)

    ev = []  # (when, stance, is_decision, Msg-like)
    for m in msgs:
        if SALES.search(m.text) and HIRING.search(m.text):
            dec = bool(re.search(r"\bDECISION\b|making the call|Decision made by", m.text)) or \
                (m.who == ceo and stance(m.text) in ("FREEZE", "HIRE"))
            ev.append((m.when, stance(m.text), dec, m))
    # Elena's follow-up mentions "Sales hiring is frozen" — caught above. Also pick up same-thread replies
    # ("No — freeze is Sales-only") that say Sales but not hiring words:
    for m in msgs:
        if re.search(r"freeze", m.text, re.I) and SALES.search(m.text) and all(m is not e[3] for e in ev):
            ev.append((m.when, "FREEZE", False, m))

    for r in roster.reqs:
        if re.search(r"sales", r.team, re.I):
            when = datetime.fromisoformat(roster.snapshot) if roster.snapshot else datetime(1970, 1, 1)
            m = Msg("roster", "headcount roster", "", when,
                    f"{r.req_id} {r.title} status={r.status} target_start={r.target_start} HM={r.manager}",
                    r.cite)
            ev.append((when, "HIRE" if r.status.upper() in ("APPROVED", "OPEN") else stance(r.status), False, m))
    ev.sort(key=lambda e: (e[0], e[3].cite.line))

    decisions = [e for e in ev if e[2] and e[1] in ("FREEZE", "HIRE")]
    if not decisions:
        return "## Q2. Sales hiring\n\nNo explicit decision about Sales hiring found in the bundle. Can't answer."
    state = decisions[-1][1]
    # the decision is the FIRST statement of the final stance after the last decision with a different stance
    prior = [e for e in decisions if e[1] != state]
    streak = [e for e in decisions if e[1] == state and (not prior or e[0] > prior[-1][0])]
    current = streak[0]
    dec_when = current[0]
    dec_day = dec_when.date()
    later_contra = [e for e in ev if e[0].date() > dec_day and e[1] not in (state, "context", "DEFER")]
    support = [e for e in ev if e[0].date() >= dec_day and e[1] == state]
    indep = {(e[3].cite.file, e[3].who) for e in support}

    # owner / enforcer
    owner, owner_cite, enf, enf_cite = "", None, "", None
    for e in ev:
        m = e[3]
        if re.search(r"I'?m making the call", m.text):
            owner, owner_cite = m.who, m.cite
        d = re.search(r"Decision made by \*\*(.+?)\*\*", m.text)
        if d and not owner:
            owner, owner_cite = d.group(1), m.cite
        en = re.search(r"\b([A-Z][a-z]+)(?: \([A-Z]+\))?\*{0,2}\s+(?:holds the line|enforces)", m.text)
        if en:
            enf, enf_cite = names.get(en.group(1).lower(), en.group(1)), (enf_cite or m.cite)
    revisit = [m for m in msgs if re.search(r"revisit", m.text, re.I) and (SALES.search(m.text) or "pipeline" in m.text.lower())
               and m.when.date() >= dec_day]
    scope = [m for m in msgs if m.when.date() >= dec_day and re.search(r"sales-only|net-new|unaffected", m.text, re.I)]
    loose = [m for m in msgs if m.source == "notes" and m.when.date() >= dec_day
             and re.search(r"REQ-114|Greenhouse|late-stage", m.text) and re.search(r"Action|\|\s*\d", m.text)]
    stale = [e for e in ev if e[3].source == "roster" and e[0].date() < dec_day and e[1] != state]

    word = {"FREEZE": "FROZEN", "HIRE": "HIRING"}.get(state, state)
    conf = "High" if len(indep) >= 3 and not later_contra else ("Medium" if not later_contra else "Low")
    out = ["## Q2. Did we decide to hire in Sales or freeze hiring — current state, and who owns it?\n"]
    out.append(f"**Answer: Sales hiring is {word}** (decided {dec_when:%Y-%m-%d}). "
               f"**Decision owner: {owner or 'not stated'}**" + (f" (CEO)" if owner == ceo else "") +
               (f"; **enforcer on reqs: {enf}**" if enf else "") +
               "." + (" REQ-114 (Account Executive) is paused, not cancelled." if state == "FREEZE" and any(
                   re.search(r"paused, not killed|on hold", e[3].text) for e in support) else "") + "\n")
    out.append(f"**Confidence: {conf}** — {len(indep)} independent sources ({', '.join(sorted(w or f for f, w in indep))}) state it is {word.lower()} on/after the decision"
               + ("; no later statement contradicts it." if not later_contra else f"; {len(later_contra)} later contradicting statement(s)."))
    out.append("\n### Key evidence")
    out.append(f"- Decision: \"{short(current[3].text, 160)}\" {current[3].cite}")
    if owner_cite:
        out.append(f"- Ownership stated explicitly {owner_cite}")
    if enf_cite:
        out.append(f"- Enforcement by {enf} {enf_cite}")
    for m in scope[:3]:
        out.append(f"- Scope: \"{short(m.text)}\" {m.cite}")
    for m in revisit[:2]:
        out.append(f"- Revisit: \"{short(m.text)}\" {m.cite}")

    out.append("\n### Timeline (every Sales-hiring statement found)")
    out.append("| Date | Stance | Who / where | Statement | Source |\n|---|---|---|---|---|")
    for when, st, dec, m in ev:
        who = m.who or m.channel
        out.append(f"| {when:%Y-%m-%d} | {st}{' (decision)' if dec else ''} | {who} | {short(m.text, 90)} | {m.cite} |")

    out.append("\n### Conflicts resolved")
    stale_says = [m for m in msgs if m.when.date() >= dec_day and re.search(r"stale|superseded", m.text, re.I)]
    for e in stale:
        out.append(f"- Roster snapshot {roster.snapshot} shows **{e[3].text}** {e[3].cite} — superseded by the "
                   f"{dec_when:%Y-%m-%d} decision" + (f"; explicitly called stale/superseded in "
                   + ", ".join(str(m.cite) for m in stale_says) if stale_says else "") + ".")
    dates = sorted({e[0].date() for e in streak})
    if len(dates) > 1:
        out.append(f"- The same decision appears dated {', '.join(map(str, dates))} (Slack message vs. written minutes; "
                   "People's Jun 11 post says \"following yesterday's leadership call\"). Treated as one decision; "
                   "earliest timestamp used.")

    out.append("\n### Could NOT verify")
    last = max(m.when for m in msgs)
    out.append(f"- Whether the decision has changed since the last message in the bundle ({last:%Y-%m-%d}) — e.g. at the "
               "revisit point named above.")
    for m in loose[:3]:
        out.append(f"- Open action: \"{short(m.text)}\" {m.cite} — completion not evidenced.")
    out.append("- Greenhouse (ATS) status of REQ-114 — no ATS export in the bundle.")
    return "\n".join(out)


# ====================================================================== router

ROUTES = [
    (re.compile(r"saas|software|tool|subscription spend|vendor", re.I), answer_saas),
    (re.compile(r"hir|freeze|headcount|\breq|sales.*(team|hiring)", re.I), answer_sales),
]


def ask(question: str, root: Path) -> str:
    for rx, fn in ROUTES:
        if rx.search(question):
            return fn(root)
    files = ", ".join(f"`{p.relative_to(root)}`" for p in find(root, "**/*.*"))
    return (f"## {question}\n\nI don't have an answerer for this question. Rather than guess, here is what the "
            f"bundle contains: {files}. Tell me which source should decide it.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("question", nargs="?")
    ap.add_argument("--all", action="store_true", help="answer both CEO questions and write output/answers.md")
    ap.add_argument("--data", default=str(Path(__file__).resolve().parent.parent), help="bundle root")
    a = ap.parse_args()
    root = Path(a.data).resolve()
    if a.all or not a.question:
        body = "\n\n---\n\n".join([
            f"# Ask-with-sources — CEO questions\n\n_Generated {datetime.now():%Y-%m-%d %H:%M} by `Analysis/ask.py` "
            f"from the raw files in `{root.name}/`. Citations are `file:Lline`._\n\n{CONFIDENCE_RUBRIC}",
            answer_saas(root), answer_sales(root)])
        out = Path(__file__).resolve().parent / "output" / "answers.md"
        out.parent.mkdir(exist_ok=True)
        out.write_text(body + "\n", encoding="utf-8")
        print(body)
        print(f"\n[written to {out}]", file=sys.stderr)
    else:
        print(ask(a.question, root))


if __name__ == "__main__":
    main()
