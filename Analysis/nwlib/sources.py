"""Load the Northwind bundle with line-level provenance.

Every value that leaves this module carries a Cite(file, line, who, when) so answers can
point at the exact file/line/message. Standard library only.
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


@dataclass(frozen=True)
class Cite:
    file: str
    line: int
    who: str = ""
    when: str = ""

    def __str__(self) -> str:
        extra = ", ".join(x for x in (self.who, self.when) if x)
        return f"`{self.file}:L{self.line}`" + (f" ({extra})" if extra else "")


@dataclass
class Doc:
    rel: str          # path relative to bundle root, used in citations
    lines: list[str]  # 1-indexed via line(n)
    encoding: str

    def line(self, n: int) -> str:
        return self.lines[n - 1]


def read_text(path: Path) -> tuple[str, str]:
    """Decode a file, handling the UTF-16 file in the bundle (see build log JC-01)."""
    raw = path.read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16"), "utf-16"
    if raw[:3] == b"\xef\xbb\xbf":
        return raw[3:].decode("utf-8"), "utf-8-sig"
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return raw.decode("cp1252"), "cp1252"


def load_doc(root: Path, path: Path) -> Doc:
    text, enc = read_text(path)
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return Doc(str(path.relative_to(root)).replace("\\", "/"), lines, enc)


def find(root: Path, pattern: str) -> list[Path]:
    return sorted(p for p in root.glob(pattern) if p.is_file() and "Analysis" not in p.parts
                  and not any(part.startswith(".") for part in p.relative_to(root).parts))


# ---------------------------------------------------------------- money

@dataclass
class Amount:
    raw: str
    value: float | None
    currency: str  # "USD", "EUR", "GBP", "" (blank)


def parse_amount(raw: str) -> Amount:
    s = (raw or "").strip()
    if not s:
        return Amount(raw, None, "")
    cur = "USD"
    if "€" in s or s.upper().startswith("EUR"):
        cur = "EUR"
    elif "£" in s or s.upper().startswith("GBP"):
        cur = "GBP"
    num = re.sub(r"[^\d.\-]", "", s)
    try:
        return Amount(raw, float(num), cur)
    except ValueError:
        return Amount(raw, None, cur)


# ---------------------------------------------------------------- P&L

@dataclass
class PnlRow:
    category: str
    item: str
    amount: Amount
    notes: str
    cite: Cite


def load_pnl(root: Path) -> list[PnlRow]:
    files = find(root, "*pnl*.csv") or find(root, "*p&l*.csv")
    if not files:
        return []
    doc = load_doc(root, files[0])
    out = []
    for n, text in enumerate(doc.lines, 1):
        if n == 1 or not text.strip():
            continue
        cols = next(csv.reader(io.StringIO(text)))
        cols += [""] * (4 - len(cols))
        out.append(PnlRow(cols[0].strip(), cols[1].strip(), parse_amount(cols[2]), cols[3].strip(),
                          Cite(doc.rel, n)))
    return out


# ---------------------------------------------------------------- roster

@dataclass
class Req:
    req_id: str
    team: str
    title: str
    status: str
    target_start: str
    manager: str
    cite: Cite


@dataclass
class Roster:
    snapshot: str
    cite_snapshot: Cite | None
    reqs: list[Req] = field(default_factory=list)


def load_roster(root: Path) -> Roster:
    files = find(root, "*roster*.csv")
    if not files:
        return Roster("", None)
    doc = load_doc(root, files[0])
    r = Roster("", None)
    section = ""
    header: list[str] = []
    for n, text in enumerate(doc.lines, 1):
        cols = next(csv.reader(io.StringIO(text))) if text.strip() else []
        if not cols:
            continue
        if cols[0].strip().lower() == "snapshot_date":
            r.snapshot, r.cite_snapshot = cols[1].strip(), Cite(doc.rel, n)
        elif cols[0].strip().upper() == "SECTION":
            section, header = cols[1].strip().upper(), []
        elif section == "OPEN_REQUISITIONS":
            if not header:
                header = [c.strip().lower() for c in cols]
                continue
            d = dict(zip(header, [c.strip() for c in cols]))
            r.reqs.append(Req(d.get("req_id", ""), d.get("team", ""), d.get("title", ""),
                              d.get("status", ""), d.get("target_start", ""),
                              d.get("hiring_manager", ""), Cite(doc.rel, n)))
    return r


# ---------------------------------------------------------------- messages (Slack + meeting notes)

@dataclass
class Msg:
    source: str      # "slack" | "notes"
    channel: str     # "#leadership" or meeting title
    who: str
    when: datetime
    text: str
    cite: Cite


SLACK_HEAD = re.compile(r"^\*\*(?P<who>[^*]+)\*\*\s+[—-]\s+\w{3}\s+(?P<mon>\w{3})\s+(?P<day>\d{1,2}),\s+"
                        r"(?P<h>\d{1,2}):(?P<m>\d{2})\s*(?P<ap>AM|PM)", re.I)


def load_slack(root: Path) -> list[Msg]:
    out: list[Msg] = []
    for path in find(root, "*slack*.md"):
        doc = load_doc(root, path)
        year = 2026
        m = re.search(r"(20\d\d)-\d\d-\d\d", "\n".join(doc.lines[:6]))
        if m:
            year = int(m.group(1))
        channel = ""
        cur = None
        for n, text in enumerate(doc.lines, 1):
            if text.startswith("## #"):
                channel = text[3:].strip()
                continue
            h = SLACK_HEAD.match(text.strip())
            if h:
                hour = int(h["h"]) % 12 + (12 if h["ap"].upper() == "PM" else 0)
                cur = (h["who"].strip(), datetime(year, MONTHS[h["mon"].lower()[:3]], int(h["day"]), hour, int(h["m"])))
                continue
            if cur and text.strip() and not text.startswith(("---", "#", ">", "*End")):
                who, when = cur
                out.append(Msg("slack", channel, who, when, text.strip(),
                               Cite(doc.rel, n, who, when.strftime("%Y-%m-%d %H:%M"))))
    return out


def load_notes(root: Path) -> list[Msg]:
    out: list[Msg] = []
    for path in find(root, "meeting_notes/*.md"):
        doc = load_doc(root, path)
        m = re.search(r"(20\d\d-\d\d-\d\d)", path.name)
        d = datetime.fromisoformat(m.group(1)) if m else datetime(1970, 1, 1)
        title = doc.lines[0].lstrip("# ").strip() if doc.lines else path.stem
        scribe = ""
        for t in doc.lines[:12]:
            s = re.search(r"\*\*(?:Notes|Note-taker|Scribe):\*\*\s*([^\n(]+)", t)
            if s:
                scribe = s.group(1).strip()
        for n, text in enumerate(doc.lines, 1):
            if text.strip() and not text.startswith(("#", "---", "|---")):
                out.append(Msg("notes", title, scribe, d, text.strip(),
                               Cite(doc.rel, n, f"minutes by {scribe}" if scribe else "", d.date().isoformat())))
    return out


def load_tickets(root: Path) -> tuple[Doc | None, list[dict]]:
    files = find(root, "*ticket*.csv")
    if not files:
        return None, []
    doc = load_doc(root, files[0])
    reader = csv.DictReader(io.StringIO("\n".join(doc.lines)))
    rows = []
    for i, r in enumerate(reader, 2):
        if not any((v or "").strip() for v in r.values()):
            continue
        r["_line"] = i
        rows.append(r)
    return doc, rows


def as_date(s: str) -> date | None:
    try:
        return date.fromisoformat((s or "").strip())
    except ValueError:
        return None
