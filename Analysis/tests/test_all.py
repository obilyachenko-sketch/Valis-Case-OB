"""Acceptance tests. Run:  python -m unittest discover -s Analysis/tests -v

"Answer-complete" means: every input row is accounted for (processed or quarantined with a reason),
the before number reproduces from the raw CSV, every deflected ticket has an action, and the ask
slice cites file:line for each answer and changes its answer when the underlying data changes.
"""
import csv
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

A = Path(__file__).resolve().parent.parent
ROOT = A.parent
sys.path.insert(0, str(A))
sys.path.insert(0, str(A / "automation"))
import ask  # noqa: E402
import support_autopilot as sa  # noqa: E402

CFG = json.loads((A / "automation" / "playbooks.json").read_text(encoding="utf-8"))
TICKETS = ROOT / "support_tickets_q1_2026.csv"


class AutopilotOnBundle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = Path(tempfile.mkdtemp())
        cls.s = sa.run(TICKETS, CFG, cls.out)
        cls.rows = list(csv.DictReader(TICKETS.open(encoding="utf-8")))
        cls.dec = list(csv.DictReader((cls.out / "ticket_decisions.csv").open(encoding="utf-8")))
        cls.box = [json.loads(l) for l in (cls.out / "outbox.jsonl").open(encoding="utf-8")]

    def test_every_row_accounted_for(self):
        self.assertEqual(self.s["processed"] + self.s["quarantined"], len(self.rows))
        self.assertEqual(sorted(d["Ticket_ID"] for d in self.dec),
                         sorted(r["Ticket_ID"] for r in self.rows))

    def test_before_reproduces_from_raw_csv(self):
        self.assertEqual(self.s["before_minutes"], sum(int(r["Handle_Minutes"]) for r in self.rows))
        self.assertEqual(self.s["before_minutes"], 4230)

    def test_every_deflected_ticket_has_an_action_and_only_those(self):
        deflected = {d["Ticket_ID"] for d in self.dec if d["route"] != "HUMAN"}
        acted = {a["ticket"] for a in self.box}
        self.assertEqual(deflected, acted)
        for d in self.dec:
            if d["route"] != "HUMAN":
                self.assertIn(d["Category"], CFG["playbooks"])

    def test_out_of_scope_unchanged_and_after_lower(self):
        for d in self.dec:
            if d["route"] == "HUMAN":
                self.assertEqual(float(d["before_min"]), float(d["after_min"]))
        self.assertLess(self.s["after_minutes"], self.s["before_minutes"])

    def test_report_written(self):
        rep = (self.out / "report.md").read_text(encoding="utf-8")
        self.assertIn("Before → after", rep)
        self.assertIn("Assumptions", rep)


class AutopilotOnDirtyInput(unittest.TestCase):
    def test_bad_rows_quarantined_not_dropped_and_utf16_ok(self):
        d = Path(tempfile.mkdtemp())
        f = d / "fresh.csv"
        body = ("Ticket_ID,Date,Category,Submitted_By,Assigned_To,Handle_Minutes,Status\n"
                "TCK-9001,2026-04-01,Thumbnail re-upload,creator_a,Ops Support,20,Closed\n"
                "TCK-9001,2026-04-01,Thumbnail re-upload,creator_a,Ops Support,20,Closed\n"   # duplicate
                "TCK-9002,2026-13-02,Tax form (W-9/W-8),creator_b,,40,Closed\n"              # bad date
                "TCK-9003,2026-04-02,Payout question,creator_c,Ops Support,-5,Closed\n"       # bad minutes
                "TCK-9004,2026-04-03,,creator_d,Ops Support,10,Open\n"                       # blank category
                "TCK-9005,2026-04-03,Brand new category,creator_e,Ops Support,30,Open\n")    # unknown -> human
        f.write_bytes(body.encode("utf-16"))
        s = sa.run(f, CFG, d / "out")
        self.assertEqual((s["input_rows"], s["processed"], s["quarantined"]), (6, 2, 4))
        q = (d / "out" / "quarantine.csv").read_text(encoding="utf-8")
        for reason in ("duplicate Ticket_ID", "bad Date", "Handle_Minutes out of 1-480", "blank Category"):
            self.assertIn(reason, q)
        with (d / "out" / "ticket_decisions.csv").open(encoding="utf-8") as fh:
            dec = list(csv.DictReader(fh))
        self.assertEqual({x["Ticket_ID"]: x["route"] for x in dec},
                         {"TCK-9001": "SELF_SERVE_THUMBNAIL", "TCK-9005": "HUMAN"})

    def test_missing_column_fails_loudly(self):
        d = Path(tempfile.mkdtemp())
        f = d / "bad.csv"
        f.write_text("Ticket_ID,Date,Category\nTCK-1,2026-01-01,X\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            sa.run(f, CFG, d / "out")


class AskSlice(unittest.TestCase):
    def test_saas_answer_and_citations(self):
        t = ask.answer_saas(ROOT)
        self.assertIn("$81,000", t)
        self.assertIn("$73,500", t)
        for cite in ("pnl_q1_2026.csv:L12", "pnl_q1_2026.csv:L13", "pnl_q1_2026.csv:L24", "slack_export.md:L144"):
            self.assertIn(cite, t)
        self.assertIn("Could NOT verify", t)

    def test_sales_answer_and_citations(self):
        t = ask.answer_sales(ROOT)
        self.assertIn("FROZEN", t)
        self.assertIn("Decision owner: Dana Whitfield", t)
        self.assertIn("Priya Raman", t)
        self.assertIn("slack_export.md:L67", t)
        self.assertIn("headcount_roster.csv:L22", t)   # stale roster surfaced as a conflict
        self.assertRegex(t, r"Confidence: High")

    def test_every_citation_points_at_a_real_line(self):
        for t in (ask.answer_saas(ROOT), ask.answer_sales(ROOT)):
            for f, n in re.findall(r"`([\w./-]+\.(?:md|csv)):L(\d+)`", t):
                lines = ask.load_doc(ROOT, ROOT / f).lines
                self.assertTrue(lines[int(n) - 1].strip(), f"{f}:L{n} is blank")


class ValueNumber(unittest.TestCase):
    def test_reproduces_from_raw_rows(self):
        import value_number
        r = value_number.main()
        self.assertEqual(r["minutes"], 4230)
        self.assertEqual(r["avoided_per_year"], 3120000 / 300 * 4)
        self.assertAlmostEqual(r["measured_h_per_week"], 4230 / 60 / 13, places=2)
        self.assertGreater(r["worst_case_h_per_week"], r["worst_case_with_autopilot"])


class FreshFileMutation(unittest.TestCase):
    """The answers must come from the data, not be hard-coded: change the data, the answer changes."""

    def setUp(self):
        self.d = Path(tempfile.mkdtemp()) / "bundle"
        shutil.copytree(ROOT, self.d, ignore=shutil.ignore_patterns(".git", "Analysis"))

    def test_saas_dedup_fixed_upstream(self):
        p = self.d / "pnl_q1_2026.csv"
        txt = p.read_text(encoding="utf-8")
        txt = txt.replace("Software & SaaS,Amplitude Analytics,7500,Product analytics\n", "")
        txt = txt.replace("Software & SaaS subtotal,81000", "Software & SaaS subtotal,73500")
        p.write_text(txt, encoding="utf-8")
        t = ask.answer_saas(self.d)
        self.assertIn("**Answer: $73,500**", t)
        self.assertNotIn("double-count", t)

    def test_sales_freeze_lifted_later(self):
        p = self.d / "slack_export.md"
        txt = p.read_text(encoding="utf-8")
        txt = txt.replace("*End of export.*",
                          "## #leadership\n\n**Dana Whitfield** — Tue Jun 16, 8:00 AM\n"
                          "Pipeline recovered. Lifting the freeze: REQ-114 approved again, let's get an AE seated.\n\n"
                          "*End of export.*")
        p.write_text(txt, encoding="utf-8")
        t = ask.answer_sales(self.d)
        self.assertIn("Sales hiring is HIRING", t)


if __name__ == "__main__":
    unittest.main()
