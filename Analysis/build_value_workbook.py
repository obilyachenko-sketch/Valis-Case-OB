#!/usr/bin/env python3
"""Build "Analysis/output/Value number raw data.xlsx" — CFO worksheet for the support-hire-avoided number.
Every calculated figure is a live formula on the raw ticket rows. Usage: python Analysis/build_value_workbook.py
"""
from __future__ import annotations

import json
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
from nwlib.sources import load_doc, load_tickets  # noqa: E402

F = "Arial"
H_FONT = Font(name=F, bold=True, color="FFFFFF")
H_FILL = PatternFill("solid", fgColor="1F3864")
BASE = Font(name=F, size=10)
BOLD = Font(name=F, size=10, bold=True)
BLUE = Font(name=F, size=10, color="0000FF")
GREEN = Font(name=F, size=10, color="008000")
TITLE = Font(name=F, size=14, bold=True)
SMALL = Font(name=F, size=9, italic=True)
RED_FILL = PatternFill("solid", fgColor="F8CBAD")
AMBER_FILL = PatternFill("solid", fgColor="FFE699")
YELLOW = PatternFill("solid", fgColor="FFFF00")
SECTION = PatternFill("solid", fgColor="D9E1F2")
THIN = Border(bottom=Side(style="thin", color="BFBFBF"))
WRAP = Alignment(wrap_text=True, vertical="top")
USD = '$#,##0;($#,##0);"-"'
H1 = '#,##0.0'
H2 = '#,##0.00'
PCT = '0.0%'


def note(cell, text):
    c = Comment(text, "Analysis")
    c.width, c.height = 380, 140
    cell.comment = c


def header(ws, row, cols, widths):
    for i, (c, w) in enumerate(zip(cols, widths), 1):
        cell = ws.cell(row=row, column=i, value=c)
        cell.font, cell.fill, cell.alignment = H_FONT, H_FILL, Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(row=row + 1, column=1)


def put(ws, r, label, val, fmt=None, font=BASE, src="", c=2):
    ws.cell(row=r, column=1, value=label).font = BASE
    cell = ws.cell(row=r, column=c, value=val)
    cell.font = font
    if fmt:
        cell.number_format = fmt
    s = ws.cell(row=r, column=c + 1, value=src)
    s.font, s.alignment = BASE, WRAP
    return cell


def section(ws, r, text, ncol=3):
    ws.cell(row=r, column=1, value=text).font = BOLD
    for j in range(1, ncol + 1):
        ws.cell(row=r, column=j).fill = SECTION


def main() -> Path:
    tdoc, rows = load_tickets(ROOT)
    slack = load_doc(ROOT, ROOT / "slack_export.md")
    pnl = load_doc(ROOT, ROOT / "pnl_q1_2026.csv")
    roster = load_doc(ROOT, ROOT / "headcount_roster.csv")
    ap = json.loads((A / "automation" / "playbooks.json").read_text())
    wb = Workbook()

    # ============================================================ Tickets (raw)
    tk = wb.create_sheet("Tickets (raw)")
    tk["A1"] = f"Raw export: {tdoc.rel} — all {len(rows)} rows as delivered. Month and ISO week are formulas; Flag/Comment are mine."
    tk["A1"].font = BOLD
    header(tk, 2, ["Source line", "Ticket_ID", "Date", "Category", "Submitted_By", "Assigned_To", "Handle_Minutes",
                   "Status", "Month", "ISO week", "Flag", "Comment"],
           [8, 11, 11, 20, 24, 13, 10, 8, 9, 8, 13, 60])
    prev = None
    for i, r in enumerate(rows):
        rr = i + 3
        d = date.fromisoformat(r["Date"])
        vals = [r["_line"], r["Ticket_ID"], d, r["Category"], r["Submitted_By"], r["Assigned_To"] or None,
                int(r["Handle_Minutes"]), r["Status"], f'=TEXT(C{rr},"yyyy-mm")', f"=WEEKNUM(C{rr},21)"]
        for j, v in enumerate(vals, 1):
            c = tk.cell(row=rr, column=j, value=v)
            c.font, c.border = BASE, THIN
        tk.cell(row=rr, column=3).number_format = "yyyy-mm-dd"
        flags = []
        if not r["Assigned_To"]:
            flags.append(("DATA QUALITY", "Assigned_To blank. Kept: effort is still logged in Handle_Minutes."))
        if r["Status"] == "Open":
            flags.append(("OPEN", "Still open at quarter end; minutes may grow. Kept as logged."))
        if prev and d < prev:
            flags.append(("BACK-FILLED", f"Dated {d} but appended after the 2026-03-31 tickets — one of 10 rows (TCK-1131–1140, 235 min) "
                                         "added late. Not a duplicate: no earlier ticket from this creator. Kept."))
        prev = max(prev, d) if prev else d
        if flags:
            tk.cell(row=rr, column=11, value=" / ".join(f for f, _ in flags)).font = BOLD
            tk.cell(row=rr, column=12, value=" ".join(t for _, t in flags)).font = BASE
            for j in (2, 11):
                tk.cell(row=rr, column=j).fill = AMBER_FILL
    n0, n1 = 3, len(rows) + 2
    T = lambda col: f"'Tickets (raw)'!${col}${n0}:${col}${n1}"  # noqa: E731

    # ============================================================ Sources
    so = wb.create_sheet("Sources")
    so["A1"] = "Every non-ticket input, quoted verbatim from its file and line. Column D holds the number the Summary uses."
    so["A1"].font = BOLD
    header(so, 2, ["File", "Line", "Raw text (verbatim)", "Value used", "Used for"], [24, 6, 90, 14, 40])
    src_rows = [
        ("pnl_q1_2026.csv", 7, pnl.line(7), 3120000, "Loaded personnel cost, Q1"),
        ("headcount_roster.csv", 18, roster.line(18), 300, "Headcount (FTE)"),
        ("slack_export.md", 176, slack.line(176), 40, "Claimed support load, h/week (Liam, May 6)"),
        ("slack_export.md", 188, slack.line(188), 1, "FTE requested ('a full-time person's worth')"),
        ("slack_export.md", 179, slack.line(179), None, "People gates the hire on measured ticket data"),
        ("slack_export.md", 185, slack.line(185), None, "Data offers ticket numbers; expects felt > measured"),
        ("slack_export.md", 193, slack.line(193), 47, "Thumbnail requests in one week, May 21 (stress test)"),
        ("slack_export.md", 244, slack.line(244), None, "Decision timing: Q3 headcount asks due end of June"),
        ("Analysis/automation/playbooks.json", None, "fallback_rate / Thumbnail residual_minutes", None,
         "Automation assumptions (not bundle data) — see Stress tests"),
    ]
    for i, (f, ln, raw, v, use) in enumerate(src_rows, 3):
        for j, val in enumerate([f, ln, raw.strip(), v, use], 1):
            c = so.cell(row=i, column=j, value=val)
            c.font, c.alignment, c.border = BASE, WRAP, THIN
        if v is not None:
            so.cell(row=i, column=4).font = BLUE
            so.cell(row=i, column=4).number_format = "#,##0"
    S_COST, S_HC, S_CLAIM, S_FTEREQ, S_47 = "Sources!$D$3", "Sources!$D$4", "Sources!$D$5", "Sources!$D$6", "Sources!$D$9"

    # ============================================================ Breakdown
    bd = wb.create_sheet("Breakdown")
    bd["A1"] = "Ticket totals by category, month and ISO week — all COUNTIFS/SUMIFS on 'Tickets (raw)'."
    bd["A1"].font = BOLD
    for col, w in zip("ABCDEF", (28, 10, 12, 10, 12, 12)):
        bd.column_dimensions[col].width = w
    cats = sorted({r["Category"] for r in rows}, key=lambda c: -sum(int(x["Handle_Minutes"]) for x in rows if x["Category"] == c))
    r = 3
    for j, h in enumerate(["Category", "Tickets", "Minutes", "Hours", "Share of time", "Avg min/ticket"], 1):
        c = bd.cell(row=r, column=j, value=h)
        c.font, c.fill = H_FONT, H_FILL
    cat_first = r + 1
    for k, cat in enumerate(cats):
        rr = r + 1 + k
        bd.cell(row=rr, column=1, value=cat).font = BASE
        bd.cell(row=rr, column=2, value=f'=COUNTIFS({T("D")},A{rr})').font = BASE
        bd.cell(row=rr, column=3, value=f'=SUMIFS({T("G")},{T("D")},A{rr})').font = BASE
        bd.cell(row=rr, column=4, value=f"=C{rr}/60").number_format = H1
        bd.cell(row=rr, column=5, value=f"=C{rr}/$C${r + 1 + len(cats)}").number_format = PCT
        bd.cell(row=rr, column=6, value=f"=C{rr}/B{rr}").number_format = H1
    tot = r + 1 + len(cats)
    bd.cell(row=tot, column=1, value="Total").font = BOLD
    for j, col in ((2, "B"), (3, "C")):
        bd.cell(row=tot, column=j, value=f"=SUM({col}{cat_first}:{col}{tot - 1})").font = BOLD
    bd.cell(row=tot, column=4, value=f"=C{tot}/60").number_format = H1
    bd.cell(row=tot, column=4).font = BOLD
    bd.cell(row=tot, column=5, value=f"=C{tot}/C{tot}").number_format = PCT
    thumb_row = cat_first + cats.index("Thumbnail re-upload")
    tax_row = cat_first + cats.index("Tax form (W-9/W-8)")

    r = tot + 3
    for j, h in enumerate(["Month", "Tickets", "Minutes", "Hours"], 1):
        c = bd.cell(row=r, column=j, value=h)
        c.font, c.fill = H_FONT, H_FILL
    months = sorted({x["Date"][:7] for x in rows})
    for k, m in enumerate(months):
        rr = r + 1 + k
        bd.cell(row=rr, column=1, value=m).font = BASE
        bd.cell(row=rr, column=2, value=f'=COUNTIFS({T("I")},A{rr})')
        bd.cell(row=rr, column=3, value=f'=SUMIFS({T("G")},{T("I")},A{rr})')
        bd.cell(row=rr, column=4, value=f"=C{rr}/60").number_format = H1
    m_first, m_last = r + 1, r + len(months)

    r = m_last + 3
    for j, h in enumerate(["ISO week", "Thumbnail tickets"], 1):
        c = bd.cell(row=r, column=j, value=h)
        c.font, c.fill = H_FONT, H_FILL
    weeks = sorted({date.fromisoformat(x["Date"]).isocalendar()[1] for x in rows})
    for k, wk in enumerate(weeks):
        rr = r + 1 + k
        bd.cell(row=rr, column=1, value=wk).font = BASE
        bd.cell(row=rr, column=2, value=f'=COUNTIFS({T("J")},A{rr},{T("D")},"Thumbnail re-upload")')
    w_first, w_last = r + 1, r + len(weeks)
    bd.cell(row=w_last + 1, column=1, value="Busiest week").font = BOLD
    bd.cell(row=w_last + 1, column=2, value=f"=MAX(B{w_first}:B{w_last})").font = BOLD
    busiest = f"Breakdown!$B${w_last + 1}"

    # ============================================================ Summary (inputs + calc)
    s = wb.active
    s.title = "Summary"
    for col, w in zip("ABC", (50, 16, 92)):
        s.column_dimensions[col].width = w
    s["A1"] = "Value number — support hire avoided (CFO worksheet)"
    s["A1"].font = TITLE
    s["A2"] = ("Blue = input with source · green = link to another tab · black = formula. Every calculated cell recomputes from "
               "'Tickets (raw)' and 'Sources'. Type: cost AVOIDANCE (req not opened), not a cut to existing spend.")
    s["A2"].font = SMALL
    section(s, 4, "Inputs")
    put(s, 5, "Claimed support load (h/week)", f"={S_CLAIM}", "#,##0", GREEN, "slack_export.md L176 (Liam, Ops): 'easily 40 hrs/week'")
    put(s, 6, "FTE requested", f"={S_FTEREQ}", "#,##0", GREEN, "slack_export.md L188: 'a full-time person's worth, minimum'")
    put(s, 7, "Weeks per quarter", 13, "#,##0", BLUE, "Finance convention (52 / 4). Data span is 12.7 weeks; using 13 is slightly conservative.")
    put(s, 8, "Hours per FTE per week", 40, "#,##0", BLUE, "Full-time week.")
    put(s, 9, "Loaded personnel cost, Q1", f"={S_COST}", USD, GREEN, "pnl_q1_2026.csv L7 — 'Salaries & benefits (all teams)', note: '~300 FTE; loaded cost'")
    put(s, 10, "Headcount (FTE)", f"={S_HC}", "#,##0", GREEN, "headcount_roster.csv L18 — TOTAL,300")
    put(s, 11, "Incremental FTE actually needed", 0, "#,##0", BLUE,
        "Judgment: current team already absorbs the load (138 of 140 Q1 tickets closed). Stress-tested on 'Stress tests'.")
    note(s["B11"], "This is the one judgment input. Set to the 'FTE needed' result (B17) for a stricter reading: value becomes (1 − 0.14) × cost.")

    section(s, 13, "Measured load (from all ticket rows)")
    put(s, 14, "Tickets, Q1 2026", f'=COUNTA({T("B")})', "#,##0", BASE, f"support_tickets_q1_2026.csv L2–L{rows[-1]['_line']}")
    put(s, 15, "Handle minutes, Q1", f'=SUM({T("G")})', "#,##0", BASE, "Sum of Handle_Minutes, every row")
    put(s, 16, "Hours per quarter", "=B15/60", H1)
    put(s, 17, "Hours per week", "=B16/B7", H2)
    put(s, 18, "FTE needed (measured)", "=B17/B8", H2)
    put(s, 19, "Claim ÷ measured", "=B5/B17", '0.0"×"', BOLD, "How far the felt load exceeds the logged load")

    section(s, 21, "Unit cost")
    put(s, 22, "Loaded cost per FTE per quarter", "=B9/B10", USD)
    put(s, 23, "Loaded cost per FTE per year", "=B22*4", USD)
    put(s, 24, "Loaded cost per hour", "=B23/(52*B8)", '$#,##0.00')

    section(s, 26, "The number")
    c = put(s, 27, "Support hire avoided, per year", "=(B6-B11)*B23", USD, Font(name=F, size=12, bold=True),
            "Formula: (FTE requested − incremental FTE needed) × loaded cost per FTE per year")
    c.fill = YELLOW
    put(s, 28, "Confidence", "Medium", None, BOLD, "High on Q1 (every row measured). Open on Q2 volume — see 'Stress tests' rows 18–23.")

    section(s, 30, "Bounds (worst case: Ops' '#47 this week' is typical for Q2)")
    put(s, 31, "Worst case — FTE needed, manual", "='Stress tests'!B21", H2, GREEN)
    put(s, 32, "Worst case — value per year, manual", "=MAX(0,B6-B31)*B23", USD, BOLD, "Half a person still avoided")
    put(s, 33, "Worst case — FTE needed, with support automation", "='Stress tests'!B23", H2, GREEN)
    put(s, 34, "Worst case — value per year, with automation", "=MAX(0,B6-B33)*B23", USD, BOLD)
    s["A36"] = ('="Answer: "&TEXT(B27,"$#,##0")&" per year — support hire avoided. Measured load "&TEXT(B17,"0.0")&" h/week ("'
                '&TEXT(B18,"0.00")&" FTE) vs "&B5&" h/week claimed. Range "&TEXT(B32,"$#,##0")&" – "&TEXT(B27,"$#,##0")&"."')
    s["A36"].font = BOLD
    s["A38"] = "Unblocker: Q2 support tickets (same columns, Apr 1 – Jun 30). Paste below row 142 on 'Tickets (raw)' and extend ranges, or rerun the builder."
    s["A38"].font = SMALL

    # ============================================================ Stress tests
    st = wb.create_sheet("Stress tests", 1)
    for col, w in zip("ABC", (58, 14, 80)):
        st.column_dimensions[col].width = w
    st["A1"] = "Where a finance person will push — each test recomputed live"
    st["A1"].font = TITLE
    section(st, 3, "Under-logging: tickets miss some effort")
    put(st, 4, "FTE needed if real effort = 2× logged", "=Summary!B17*2/Summary!B8", H2, BASE, "Still < 0.5 FTE → holds")
    put(st, 5, "FTE needed if real effort = 3× logged", "=Summary!B17*3/Summary!B8", H2, BASE, "Still < 0.5 FTE → holds")
    put(st, 6, "Share of effort tickets must capture for the 40 h claim to be true", "=Summary!B17/Summary!B5", PCT, BOLD,
        "Implausibly low without evidence of large off-ticket work")
    section(st, 8, "Seasonality and growth")
    put(st, 9, "Tax-form share of Q1 minutes (W-9/W-8 season)", f"=Breakdown!E{tax_row}", PCT, GREEN,
        "NOT a proven peak: tax forms come with new-creator onboarding (slack L171) and Ops calls June 'tax form season again' (L201). Treat as neutral.")
    put(st, 10, f"Hours, {months[0]}", f"=Breakdown!D{m_first}", H1, GREEN)
    put(st, 11, f"Hours, {months[-1]}", f"=Breakdown!D{m_last}", H1, GREEN)
    put(st, 12, "Change first → last month", "=B11/B10-1", PCT, BASE, "Flat to slightly up")
    put(st, 13, "FTE needed at 2× ticket volume", "=Summary!B18*2", H2, BASE, "Holds")
    section(st, 15, "The '#47 this week' challenge (slack_export.md L193, May 21)")
    put(st, 16, "Thumbnail requests in one week (Ops claim)", f"={S_47}", "#,##0", GREEN, "Sources row — verbatim quote there")
    put(st, 17, "Q1 average thumbnail tickets per week", f"=Breakdown!B{thumb_row}/Summary!B7", H1, GREEN)
    put(st, 18, "Q1 busiest week (thumbnail tickets)", f"={busiest}", "#,##0", GREEN, "47 would be this many times the busiest Q1 week →")
    put(st, 19, "Average minutes per thumbnail ticket", f"=Breakdown!F{thumb_row}", H1, GREEN)
    put(st, 20, "Other categories, h/week (Q1 rate)", f"=(Summary!B15-Breakdown!C{thumb_row})/60/Summary!B7", H2)
    put(st, 21, "Worst case — FTE needed, manual", "=(B16*B19/60+B20)/Summary!B8", H2, BOLD, "If every week in Q2 were like May 21")
    st["D18"] = "=B16/B18"
    st["D18"].number_format = '0.0"×"'
    st["D18"].font = BOLD
    put(st, 22, "Automation fallback rate (assumption)", ap["fallback_rate"], PCT, BLUE,
        "Analysis/automation/playbooks.json — share of deflected tickets still needing a person")
    put(st, 23, "Worst case — FTE needed, with support automation",
        f"=(B16*((1-B22)*B24+B22*B19)/60+B20)/Summary!B8", H2, BOLD, "Thumbnails deflected to self-serve; other work unchanged")
    put(st, 24, "Residual minutes per automated thumbnail (assumption)",
        ap["playbooks"]["Thumbnail re-upload"]["residual_minutes"], "#,##0", BLUE, "playbooks.json — human spot-check time")
    st["A26"] = ("Verdict: the number survives every test except a Q2 surge at the '#47' rate without automation — then about half "
                 "a person is needed and the value falls to the 'manual' bound on the Summary.")
    st["A26"].font = BOLD
    st.merge_cells("A26:C26")
    st["A26"].alignment = WRAP
    st.row_dimensions[26].height = 30

    # ============================================================ Cannot verify
    cv = wb.create_sheet("Cannot verify")
    cv["A1"] = "What I could NOT verify from the bundle — impact on the number and how to unblock."
    cv["A1"].font = BOLD
    header(cv, 2, ["#", "Not verifiable", "Why it matters", "Direction if wrong", "Unblocker"], [4, 40, 46, 26, 34])
    items = [
        ("Q2 ticket volume", "Only Q1 tickets exist; the 40 h claim and '#47' are from May. Searched folder, repo and all Slack/notes — none.",
         "Value falls toward the manual worst case", "Ben Okoro (Data) — Q2 export, same columns (slack L185)"),
        ("A formal support req", "Roster open reqs (L21–L25) list none for Ops; the ask is only in Slack.",
         "Value is a decision avoided, not a budgeted cost", "Elena / Liam: was a req drafted for Q3?"),
        ("Off-ticket effort", "Chasing by email/DM wouldn't be in Handle_Minutes.", "Load higher than logged (stress-tested 2×, 3×)",
         "Ops time study for 2 weeks"),
        ("How Handle_Minutes is captured", "All 140 values are multiples of 5 (10–55) → likely estimates, not timers.",
         "Either direction", "Ask how the ticket tool records time"),
        ("Role-specific loaded cost", "Only the company average exists ($3.12M ÷ 300). P&L says '~300 FTE', roster says 300.",
         "Dollar value moves; direction doesn't", "Finance: loaded cost for an ops coordinator"),
        ("Why 10 tickets were back-filled", "TCK-1131–1140 (235 min, 5.6% of minutes) are dated Jan–Mar but appended after Mar 31. "
         "Distinct creators, so not duplicates.", "If more late entries exist, Q1 load grows slightly", "Ask Ops when/why these were logged"),
        ("Non-creator support in the 40 h", "Ops may count work that isn't in the creator ticket log.", "Claim may be about a wider scope",
         "Ask Liam what the 40 h covers"),
    ]
    for i, row in enumerate(items, 3):
        for j, v in enumerate([i - 2, *row], 1):
            c = cv.cell(row=i, column=j, value=v)
            c.font, c.alignment, c.border = BASE, WRAP, THIN
    cv.cell(row=3, column=2).fill = RED_FILL

    # ============================================================ Alternatives
    al = wb.create_sheet("Alternatives")
    al["A1"] = "Value numbers considered and ranked lower — and why."
    al["A1"].font = BOLD
    header(al, 2, ["Candidate", "Annual value", "Arithmetic", "Source", "Why ranked lower"], [32, 14, 40, 36, 52])
    alts = [
        ("Support hire avoided (chosen)", "=Summary!B27", "1 FTE × loaded cost per FTE", "Summary", "Every input is a raw row; informs a live decision."),
        ("Amplitude duplicate closed", "=7500*4", "$7,500 per quarter × 4", "pnl_q1_2026.csv L12–L13; slack L147–L153",
         "Can't tell a cash leak from a booking error without the invoice."),
        ("Brand-deal recon time saved", "=3*12*8*Summary!B24", "3 days × 12 months × 8 h × loaded $/h",
         "slack L108, L158; finance_review L11", "Self-reported time; the 3 source exports aren't in the bundle."),
        ("Support automation hours saved", "=29.9*4*Summary!B24", "29.9 h/qtr saved (modelled) × 4 × loaded $/h",
         "output/autopilot/report.md", "Modelled, and small. Its job is to keep the hire unnecessary."),
    ]
    for i, row in enumerate(alts, 3):
        for j, v in enumerate(row, 1):
            c = al.cell(row=i, column=j, value=v)
            c.font, c.alignment, c.border = BASE, WRAP, THIN
        al.cell(row=i, column=2).number_format = USD
    al.cell(row=3, column=1).font = BOLD
    al.cell(row=3, column=2).fill = YELLOW
    note(al["B6"], "29.9 h/quarter is the modelled saving from Analysis/output/autopilot/summary.json (fallback 20%, residuals 5/10 min).")

    order = ["Summary", "Stress tests", "Tickets (raw)", "Breakdown", "Sources", "Cannot verify", "Alternatives"]
    wb._sheets = [wb[n] for n in order]
    out = A / "output" / "Value number raw data.xlsx"
    wb.save(out)
    print(out)
    return out


if __name__ == "__main__":
    main()
