#!/usr/bin/env python3
"""Build "Analysis/output/Time waste raw data.xlsx" — where Northwind loses time, ranked by business criticality.
Usage: python Analysis/build_timewaste_workbook.py
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

A = Path(__file__).resolve().parent
ROOT = A.parent
sys.path.insert(0, str(A))
from nwlib.sources import load_doc, load_notes, load_slack, load_tickets  # noqa: E402

F = "Arial"
H_FONT = Font(name=F, bold=True, color="FFFFFF")
H_FILL = PatternFill("solid", fgColor="1F3864")
BASE = Font(name=F, size=10)
BOLD = Font(name=F, size=10, bold=True)
BLUE = Font(name=F, size=10, color="0000FF")
TITLE = Font(name=F, size=14, bold=True)
SMALL = Font(name=F, size=9, italic=True)
YELLOW = PatternFill("solid", fgColor="FFFF00")
GREEN_FILL = PatternFill("solid", fgColor="C6EFCE")
AMBER_FILL = PatternFill("solid", fgColor="FFE699")
RED_FILL = PatternFill("solid", fgColor="F8CBAD")
GREY_FILL = PatternFill("solid", fgColor="EDEDED")
THIN = Border(bottom=Side(style="thin", color="BFBFBF"))
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="top")
H1 = '#,##0.0;-#,##0.0;"-"'

SL, FR, LS, DR, PNL, CEO = ("slack_export.md", "meeting_notes/finance_review_2026-05-28.md",
                            "meeting_notes/leadership_sync_2026-06-11.md", "meeting_notes/data_review_2026-05-20.md",
                            "pnl_q1_2026.csv", "CEO_CONTEXT.md")

DIMS = [
    ("Money exposure", "How much revenue or spend flows through it",
     "1 = little / indirect", "2 = creator payouts, cost lines, per-creator economics", "3 = core revenue (brand partnerships)"),
    ("Trust in the numbers", "Do errors reach leadership / board numbers?",
     "1 = no", "2 = internal reporting", "3 = board-level figures"),
    ("Deadline pressure", "Is it on a hard, recurring deadline?",
     "1 = ad hoc", "2 = recurring, soft deadline", "3 = month-end close / board"),
    ("Key-person risk", "Does it depend on one person?",
     "1 = shared team", "2 = small team", "3 = one named person"),
    ("Growth", "Does it get worse as the business grows?",
     "1 = flat", "2 = grows with creators", "3 = explicitly flagged as getting worse"),
]

# id, function, workflow, who does it, basis, automatable, data in bundle to build?, criticality scores (5) with reasons
WF = [
    ("W1", "Finance", "Brand-deal revenue reconciliation (CRM ↔ invoicing ↔ payout tracker)", "Maya Fortin (Finance Analyst)",
     "claimed", "Yes — 3-way match", "No — none of the 3 exports is in the bundle",
     [(3, "Brand partnerships = $4.2M of $5.25M revenue (80%) — pnl L2, L5"),
      (3, "Revenue figures for the board 'never tie out first pass' — finance_review L12; slack L114"),
      (3, "Every month-end close — slack L108, L158; finance_review L11"),
      (3, "Only Maya does it — slack L94, L108"),
      (3, "'only going to get worse as brand-partnership volume grows' — finance_review L13")]),
    ("W2", "Ops / support", "Tax-form chasing (W-9 / W-8)", "Ops Support (Liam Doyle's team)",
     "measured", "Yes — e-sign + reminders", "Yes — tickets",
     [(2, "Tied to creator onboarding/payouts — slack L171 (link to payout eligibility not stated in data)"),
      (1, "Doesn't feed leadership numbers"),
      (2, "Recurs with onboarding and 'tax form season' — slack L201"),
      (2, "Ops Support team — tickets Assigned_To"),
      (2, "Grows with new creators, incl. international (W-8) — slack L171, L201")]),
    ("W3", "Ops / support + Content", "Thumbnail re-uploads after publish", "Ops Support + Post-production",
     "measured", "Yes — self-serve swap", "Yes — tickets",
     [(1, "'Low dollar value per ticket' — slack L196"),
      (1, "Doesn't feed leadership numbers"),
      (1, "Ad hoc, creator-initiated — slack L165"),
      (1, "Shared between Ops and Post — slack L165, L168"),
      (2, "'piling up', '#47 this week' — slack L165, L193")]),
    ("W4", "Ops / support", "Payout questions ('where's my payout')", "Ops Support",
     "measured", "Partly — needs payout tracker", "Partly — tickets yes, payout tracker no",
     [(2, "Creator payouts; processing fees $31k/qtr — pnl L34"),
      (2, "Payout tracker is one of the 3 sources that drift — slack L100"),
      (1, "Ad hoc"),
      (1, "Ops Support team"),
      (2, "Grows with creators — slack L176")]),
    ("W5", "Ops / support", "Other support (login, account access, takedowns)", "Ops Support",
     "measured", "No — security / legal judgment", "Yes — tickets",
     [(1, "Small"), (1, "No"), (1, "Ad hoc"), (1, "Team"), (1, "Flat (Q1 data)")]),
    ("W6", "Data + Finance", "Reconciling the 'active creators' number (1,210 vs 1,840) for decks", "Ben Okoro, Maya Fortin, Priya Raman",
     "not quantified", "No — a definition decision, not automation", "Yes — but it's a decision",
     [(2, "Per-creator economics for the board built on it — finance_review L18"),
      (3, "Two numbers in board materials — data_review L18; slack L56"),
      (3, "Board update deadline — data_review L41; leadership L31"),
      (2, "Ben + Maya/Priya — leadership L31"),
      (1, "Flat")]),
    ("W7", "Content", "Post-production bottleneck (editing, re-exports)", "Yuki Tanaka's post team",
     "not quantified", "Partly", "No — no throughput data",
     [(2, "Contractor/freelance production $410k/qtr — pnl L8 (link to bottleneck not stated)"),
      (1, "No"),
      (2, "Show schedules — slack L34"),
      (2, "Post team"),
      (2, "Wants another editor — slack L250")]),
    ("W8", "Finance", "Vendor / SaaS hygiene (renewal calendar, Salesforce check, EUR, Amplitude invoice)", "Maya Fortin",
     "not quantified", "Yes — vendor calendar + checks", "Partly — P&L only, no invoices",
     [(1, "SaaS $81k/qtr; $7.5k possible duplicate — pnl L24, L12–L13"),
      (2, "SaaS line went to the board cut — slack L42, L45"),
      (2, "Renewals 'inside the next two quarters' — finance_review L24"),
      (3, "All on Maya — finance_review L36–L39"),
      (1, "Flat")]),
]

EVIDENCE = {
    "W1": [(SL, 97), (SL, 100), (SL, 108), (SL, 111), (SL, 114), (SL, 158), (FR, 11), (FR, 12), (FR, 13), (FR, 36), (LS, 35), (PNL, 2), (PNL, 5)],
    "W2": [(SL, 171), (SL, 176), (SL, 201), (SL, 204)],
    "W3": [(SL, 165), (SL, 168), (SL, 193), (SL, 196)],
    "W4": [(SL, 176), (SL, 100), (PNL, 34)],
    "W5": [],
    "W6": [(SL, 53), (SL, 59), (SL, 130), (SL, 136), (DR, 13), (DR, 16), (DR, 18), (FR, 18), (FR, 19), (LS, 30), (LS, 31)],
    "W7": [(SL, 34), (SL, 168), (SL, 250), (PNL, 8)],
    "W8": [(SL, 45), (SL, 147), (SL, 153), (FR, 23), (FR, 24), (FR, 25), (FR, 39)],
    "ALL": [(CEO, 7), (SL, 176), (SL, 179), (SL, 185)],
}
RELEVANCE = {  # short reading of each line
    (SL, 97): "Recon 'eats my life every month' — three sources never agree first pass",
    (SL, 100): "Names the 3 sources: CRM export, invoicing sheet, payout tracker; 'drift every single month'",
    (SL, 108): "April recon took ~3 full days; 'same dance every month-end'",
    (SL, 111): "CFO: 'biggest recurring time sink in finance'",
    (SL, 114): "Automating the 3-way match = 3 days/month back + trustworthy first pass",
    (SL, 158): "May close: ~3 days again; Maya's vote for automation #1",
    (FR, 11): "~3 full days this cycle, same as last few months",
    (FR, 12): "Amounts, close dates and payout splits drift; manual line-by-line tie-out",
    (FR, 13): "CFO: single biggest finance time-sink; worse as volume grows; top automation candidate",
    (FR, 36): "Action: Maya documents current recon steps before June close",
    (LS, 35): "Leadership: ~3 days/month, flagged for Marcus's ops/automation review",
    (PNL, 2): "Brand partnerships revenue $4.2M (Q1)",
    (PNL, 5): "Total revenue $5.25M (Q1)",
    (PNL, 8): "Contractor / freelance production $410k (Q1)",
    (PNL, 34): "Payout processing fees $31k (Q1)",
    (SL, 171): "Tax-form chasing for new creators, constant follow-up",
    (SL, 176): "Ops: 'easily 40 hrs/week' across thumbnails, tax forms, payout questions",
    (SL, 201): "'Tax form season again'; W-8 chasing; manual; asks for a tool",
    (SL, 204): "People: e-sign + tax form services are 'cheap'; revisit Q3",
    (SL, 165): "Thumbnail swaps piling up; all manual through the CMS",
    (SL, 168): "Post: each swap is a manual re-export, 'only a few minutes' (log says ~22 min)",
    (SL, 193): "'#47 this week'; self-serve would make 'half my tickets' vanish",
    (SL, 196): "Content: worth scoping; low $ per ticket, high annoyance",
    (SL, 53): "'Active creators' means different things to Data vs Finance",
    (SL, 59): "It's a definitional choice, not a typo",
    (SL, 130): "Finance uses 1,840 under contract as 'active roster'",
    (SL, 136): "Data's active = 1,210; keep getting mixed up",
    (DR, 13): "Data definition: posted ≥1 in 30 days = 1,210",
    (DR, 16): "Finance/Talent count the signed roster — larger number",
    (DR, 18): "CEO wants them reconciled before the board update",
    (FR, 18): "Finance models per-creator economics on 1,840",
    (FR, 19): "CEO questions the denominator; parked",
    (LS, 30): "Recurring confusion: 1,210 vs 1,840, not reconciled",
    (LS, 31): "Action: pick one definition before the board update",
    (SL, 34): "Bottleneck is post, not shooting",
    (SL, 250): "Post needs another editor — the real bottleneck",
    (SL, 45): "CFO wants a second pair of eyes on SaaS line items",
    (SL, 147): "Amplitude listed twice — unconfirmed",
    (SL, 153): "Invoice still not back; CSV left as-is",
    (FR, 23): "Salesforce: check posted vs $60k contract",
    (FR, 24): "Renewals auto-renew within two quarters; build a vendor calendar",
    (FR, 25): "EUR tools need normalising before the SaaS subtotal",
    (FR, 39): "Action: Maya builds vendor renewal calendar",
    (CEO, 7): "CEO: drowning in dashboards and status meetings; doesn't trust her numbers",
    (SL, 179): "People: is 40 h/week measured or a vibe?",
    (SL, 185): "Data expects felt volume > measured volume",
}
MISSING = [
    ("W1", "CRM deal export, invoicing sheet, payout tracker", "Can't build or test the recon automation; can't measure real recon time", "Maya Fortin / Finance"),
    ("W1", "Maya's written-up recon steps (finance_review L36, due before June close)", "Exact scope and edge cases of the automation", "Maya Fortin"),
    ("W1", "Time log for the recon", "Turns '~3 days' into a measured number (bounds 45–84 h/qtr)", "2-month time log"),
    ("W2–W5", "Q2 support tickets", "Tests Ops' May '#47 this week' surge", "Ben Okoro (Data)"),
    ("W2", "E-sign / tax-form service quotes", "Cost side of the business case (break-even ≈ $2.1k/yr on time alone)", "Elena Novak (People)"),
    ("W3", "Engineering estimate for self-serve thumbnail swap; CMS cost", "Cost side (break-even ≈ $1.8k/yr on time alone)", "Raj Patel (Eng)"),
    ("W6", "Agreed headline definition of 'active creators'", "Removes recurring deck rework", "Priya + Ben (leadership L31)"),
    ("W7", "Post-production throughput / backlog data", "Sizes the content bottleneck", "Yuki Tanaka"),
    ("W8", "Vendor invoices / contracts", "Confirms Amplitude duplicate, Salesforce posting", "AP / Maya"),
]


def note(cell, text):
    c = Comment(text, "Analysis")
    c.width, c.height = 380, 130
    cell.comment = c


def header(ws, row, cols, widths):
    for i, (c, w) in enumerate(zip(cols, widths), 1):
        cell = ws.cell(row=row, column=i, value=c)
        cell.font, cell.fill, cell.alignment = H_FONT, H_FILL, Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(row=row + 1, column=1)


def main() -> Path:
    tdoc, trows = load_tickets(ROOT)
    msgs = {(m.cite.file, m.cite.line): m for m in load_slack(ROOT) + load_notes(ROOT)}
    docs = {f: load_doc(ROOT, ROOT / f) for f in (SL, FR, LS, DR, PNL, CEO)}
    wb = Workbook()

    # ============================================================ Tickets (raw)
    tk = wb.create_sheet("Tickets (raw)")
    tk["A1"] = f"Raw export: {tdoc.rel} — all {len(trows)} rows, unchanged. Used for the measured support hours."
    tk["A1"].font = BOLD
    header(tk, 2, ["Source line", "Ticket_ID", "Date", "Category", "Submitted_By", "Assigned_To", "Handle_Minutes", "Status"],
           [8, 11, 11, 22, 24, 13, 10, 8])
    for i, r in enumerate(trows, 3):
        for j, v in enumerate([r["_line"], r["Ticket_ID"], date.fromisoformat(r["Date"]), r["Category"], r["Submitted_By"],
                               r["Assigned_To"] or None, int(r["Handle_Minutes"]), r["Status"]], 1):
            c = tk.cell(row=i, column=j, value=v)
            c.font = BASE
        tk.cell(row=i, column=3).number_format = "yyyy-mm-dd"
    t1 = len(trows) + 2
    TD, TG = f"'Tickets (raw)'!$D$3:$D${t1}", f"'Tickets (raw)'!$G$3:$G${t1}"

    # ============================================================ Evidence
    ev = wb.create_sheet("Evidence")
    ev["A1"] = "Every line used, quoted verbatim from its file. 'Supports' is my one-line reading."
    ev["A1"].font = BOLD
    header(ev, 2, ["Workflow", "File", "Line", "Who", "Date", "Raw text (verbatim)", "Supports"], [9, 34, 6, 18, 11, 80, 52])
    r = 3
    for wid, lst in EVIDENCE.items():
        for f, ln in lst:
            m = msgs.get((f, ln))
            who = (m.who if m and m.source == "slack" else (f"minutes ({m.who})" if m and m.who else "")) if m else ""
            when = m.when.date() if m else None
            raw = docs[f].line(ln).strip()
            for j, v in enumerate([wid, f, ln, who, when, raw, RELEVANCE.get((f, ln), "")], 1):
                c = ev.cell(row=r, column=j, value=v)
                c.font, c.alignment, c.border = BASE, WRAP, THIN
            ev.cell(row=r, column=5).number_format = "yyyy-mm-dd"
            r += 1
    ev_last = r - 1
    EVW = f"Evidence!$A$3:$A${ev_last}"

    # ============================================================ Criticality rubric
    rb = wb.create_sheet("Criticality rubric")
    rb["A1"] = "Business criticality — five dimensions, each scored 1–3 (max 15). Every score on 'Workflows' cites its reason."
    rb["A1"].font = BOLD
    header(rb, 2, ["Dimension", "Question", "1", "2", "3"], [22, 42, 26, 40, 36])
    for i, d in enumerate(DIMS, 3):
        for j, v in enumerate(d, 1):
            c = rb.cell(row=i, column=j, value=v)
            c.font, c.alignment, c.border = BASE, WRAP, THIN
    rb.cell(row=9, column=1, value=("Priority rule: rank by criticality score; ties broken by hours per quarter "
                                     "(sort key = score × 1000 + hours). Hours alone would rank W1 and support as a tie.")).font = SMALL

    # ============================================================ Workflows
    wf = wb.create_sheet("Workflows")
    wf["A1"] = ("Every workflow the bundle shows manual effort piling up on. Blue = typed input with source; black = formula. "
                "Criticality reasons are in the 'why' columns; definitions on 'Criticality rubric'.")
    wf["A1"].font = BOLD
    cols = ["ID", "Function", "Workflow", "Who does it", "Time basis", "Qty", "Unit", "Hours/day (assump.)", "Hours / quarter",
            "Low h/qtr", "High h/qtr", "Measured or claimed", "# sources", ] + \
           [d[0] for d in DIMS] + ["Criticality (of 15)", "Automatable?", "Data in bundle to build it?", "Sort key", "Priority rank"] + \
           [f"Why: {d[0]}" for d in DIMS]
    widths = [5, 13, 34, 20, 26, 6, 9, 9, 10, 9, 9, 11, 8] + [9] * 5 + [10, 22, 24, 9, 8] + [34] * 5
    header(wf, 2, cols, widths)
    C = {name: get_column_letter(i) for i, name in enumerate(cols, 1)}
    cat_map = {"W2": ["Tax form (W-9/W-8)"], "W3": ["Thumbnail re-upload"], "W4": ["Payout question"],
               "W5": ["Login issue", "Account access", "Content takedown"]}
    first = 3
    for i, (wid, fn, name, who, basis, auto, data, scores) in enumerate(WF, first):
        def setc(col, v, fmt=None, font=BASE, fill=None):
            c = wf[f"{C[col]}{i}"]
            c.value, c.font, c.alignment, c.border = v, font, WRAP, THIN
            if fmt:
                c.number_format = fmt
            if fill:
                c.fill = fill
            return c
        setc("ID", wid, font=BOLD)
        setc("Function", fn)
        setc("Workflow", name)
        setc("Who does it", who)
        if wid == "W1":
            setc("Time basis", "'~3 full days' per month-end (slack L108, L158; finance_review L11)")
            setc("Qty", 3, font=BLUE)
            setc("Unit", "days/month")
            setc("Hours/day (assump.)", 8, font=BLUE)
            note(wf[f"{C['Hours/day (assump.)']}{i}"], "Assumption: an 8-hour working day. Bounds use 6–8 h/day and 2.5–3.5 days.")
            setc("Hours / quarter", f"={C['Qty']}{i}*{C['Hours/day (assump.)']}{i}*3", H1, BOLD)
            setc("Low h/qtr", "=2.5*6*3", H1)
            setc("High h/qtr", "=3.5*8*3", H1)
            setc("Measured or claimed", "Claimed — same '~3 days' in Slack, finance review and leadership minutes", fill=AMBER_FILL)
        elif wid in cat_map:
            setc("Time basis", "Sum of Handle_Minutes, Q1 tickets (" + ", ".join(cat_map[wid]) + ")")
            f_ = "+".join(f'SUMIFS({TG},{TD},"{c}")' for c in cat_map[wid])
            setc("Hours / quarter", f"=({f_})/60", H1, BOLD)
            setc("Low h/qtr", f"={C['Hours / quarter']}{i}", H1)
            setc("High h/qtr", f"={C['Hours / quarter']}{i}*2", H1)
            note(wf[f"{C['High h/qtr']}{i}"], "High = 2× logged, in case tickets miss off-ticket effort (not measured).")
            setc("Measured or claimed", "Measured (ticket log)", fill=GREEN_FILL)
        else:
            setc("Time basis", "No time figure anywhere in the bundle")
            setc("Hours / quarter", None)
            setc("Measured or claimed", "Not quantified", fill=GREY_FILL)
        setc("# sources", f'=COUNTIFS({EVW},A{i})', "0")
        for k, (sc, why) in enumerate(scores):
            setc(DIMS[k][0], sc, "0", BLUE).alignment = CENTER
            setc(f"Why: {DIMS[k][0]}", why)
        setc("Criticality (of 15)", f"=SUM({C[DIMS[0][0]]}{i}:{C[DIMS[-1][0]]}{i})", "0", BOLD).alignment = CENTER
        setc("Automatable?", auto)
        setc("Data in bundle to build it?", data, fill=RED_FILL if data.startswith("No") else None)
        setc("Sort key", f"={C['Criticality (of 15)']}{i}*1000+N({C['Hours / quarter']}{i})+(100-ROW())/10000", "0.0000")
    last = first + len(WF) - 1
    for i in range(first, last + 1):
        c = wf[f"{C['Priority rank']}{i}"]
        c.value = f"=RANK({C['Sort key']}{i},${C['Sort key']}${first}:${C['Sort key']}${last})"
        c.font, c.alignment = BOLD, CENTER
    wf[f"{C['Priority rank']}{first}"].fill = YELLOW
    tr = last + 2
    wf[f"A{tr}"] = "Totals (quantified workflows)"
    wf[f"A{tr}"].font = BOLD
    for col in ("Hours / quarter", "Low h/qtr", "High h/qtr"):
        c = wf[f"{C[col]}{tr}"]
        c.value, c.number_format, c.font = f"=SUM({C[col]}{first}:{C[col]}{last})", H1, BOLD
    wf.row_dimensions[2].height = 45

    # ============================================================ Missing data
    md = wb.create_sheet("Missing data")
    md["A1"] = "What isn't in the bundle — and who can unblock it."
    md["A1"].font = BOLD
    header(md, 2, ["Workflow", "Missing", "What it would settle", "Who"], [10, 50, 54, 26])
    for i, row in enumerate(MISSING, 3):
        for j, v in enumerate(row, 1):
            c = md.cell(row=i, column=j, value=v)
            c.font, c.alignment, c.border = BASE, WRAP, THIN
        if row[0] == "W1":
            md.cell(row=i, column=1).fill = RED_FILL

    # ============================================================ Summary
    s = wb.active
    s.title = "Summary"
    for col, w in zip("ABCDEFGH", (6, 46, 12, 12, 12, 10, 30, 30)):
        s.column_dimensions[col].width = w
    s["A1"] = "Where is Northwind wasting the most time — and what to automate first?"
    s["A1"].font = TITLE
    s["A2"] = "Live view of the 'Workflows' tab, ordered by priority rank (criticality first, hours as tiebreaker). Scope: Q1 2026 tickets; Slack/notes Apr 21 – Jun 17, 2026."
    s["A2"].font = SMALL
    for j, h in enumerate(["Rank", "Workflow", "Hours / qtr", "Low", "High", "Criticality (of 15)", "Measured or claimed", "Automatable?"], 1):
        c = s.cell(row=4, column=j, value=h)
        c.font, c.fill, c.alignment = H_FONT, H_FILL, Alignment(wrap_text=True)
    W = lambda col: f"Workflows!${C[col]}${first}:${C[col]}${last}"  # noqa: E731
    for k in range(1, len(WF) + 1):
        rr = 4 + k
        s.cell(row=rr, column=1, value=k).font = BOLD
        m = f"MATCH($A{rr},{W('Priority rank')},0)"
        for j, col in ((2, "Workflow"), (3, "Hours / quarter"), (4, "Low h/qtr"), (5, "High h/qtr"), (6, "Criticality (of 15)"),
                       (7, "Measured or claimed"), (8, "Automatable?")):
            c = s.cell(row=rr, column=j, value=f'=IFERROR(INDEX({W(col)},{m})&"","")' if j in (2, 7, 8) else f'=IFERROR(IF(INDEX({W(col)},{m})="","—",INDEX({W(col)},{m})),"")')
            c.font = BOLD if k == 1 else BASE
            c.alignment = WRAP
            if j in (3, 4, 5):
                c.number_format = H1
        if k == 1:
            for j in range(1, 9):
                s.cell(row=rr, column=j).fill = YELLOW
    nr = 5 + len(WF) + 1
    lines = [
        ("Answer", BOLD),
        ("Two workflows tie on hours: brand-deal revenue reconciliation (~72 h/qtr, claimed; bounds 45–84) and creator support "
         "(70.5 h/qtr, measured). Automate the reconciliation first: it scores 15/15 on criticality — 80% of revenue, board-level "
         "numbers, every month-end close, one person, and getting worse with volume.", BASE),
        ("Catch: none of its three inputs (CRM export, invoicing sheet, payout tracker) is in the bundle — see 'Missing data'. "
         "Scope is in Analysis/automation/RECON_SCOPE.md. The support automation (tax forms + thumbnails) is what runs on this data today.", BASE),
        ("Confidence: Medium on the ranking (recon time is self-reported); High that W1 and support are the two largest — nothing else has a time figure.", BOLD),
        ("Colour key — Workflows: green = measured, amber = claimed, grey = not quantified, red = data to build it is missing. Blue numbers are inputs.", SMALL),
    ]
    for k, (t, fnt) in enumerate(lines):
        c = s.cell(row=nr + k, column=1, value=t)
        c.font, c.alignment = fnt, WRAP
        s.merge_cells(start_row=nr + k, start_column=1, end_row=nr + k, end_column=8)
        s.row_dimensions[nr + k].height = 15 if fnt is BOLD and k == 0 else 44

    wb._sheets = [wb[n] for n in ["Summary", "Workflows", "Criticality rubric", "Evidence", "Tickets (raw)", "Missing data"]]
    out = A / "output" / "Time waste raw data.xlsx"
    wb.save(out)
    print(out)
    return out


if __name__ == "__main__":
    main()
