"""Acceptance tests for the tax-form chaser — the "answer-complete" checks in TAXFORM_BUILDER_SPEC.md.
Run: python -m unittest discover -s Analysis/tests -v
"""
import csv
import filecmp
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

A = Path(__file__).resolve().parent.parent
ROOT = A.parent
sys.path.insert(0, str(A / "automation"))
sys.path.insert(0, str(A))
import taxform_chaser as tc  # noqa: E402

CFG = json.loads((A / "automation" / "taxform_config.json").read_text(encoding="utf-8"))
TICKETS = ROOT / "support_tickets_q1_2026.csv"
HEAD = "Ticket_ID,Date,Category,Submitted_By,Assigned_To,Handle_Minutes,Status\n"


def read_csv(p):
    with open(p, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class OnBundle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = Path(tempfile.mkdtemp())
        cls.s = tc.run(TICKETS, CFG, cls.out)
        cls.raw = [r for r in read_csv(TICKETS) if r["Category"].startswith("Tax form")]
        cls.tr = read_csv(cls.out / "tracker.csv")
        cls.box = [json.loads(l) for l in (cls.out / "outbox.jsonl").read_text(encoding="utf-8").splitlines()]

    def test_every_tax_ticket_becomes_exactly_one_request(self):
        self.assertEqual(len(self.raw), 36)
        self.assertEqual(sorted(t["ticket"] for t in self.tr), sorted(r["Ticket_ID"] for r in self.raw))

    def test_before_reproduces_from_raw_rows(self):
        self.assertEqual(self.s["before_minutes"], sum(int(r["Handle_Minutes"]) for r in self.raw))
        self.assertEqual(self.s["before_minutes"], 1555)

    def test_each_request_has_full_schedule_and_nothing_else(self):
        per = {}
        for e in self.box:
            per.setdefault(e["ticket"], []).append(e["type"])
        self.assertEqual(set(per), {r["Ticket_ID"] for r in self.raw})
        expected = sorted(["ESIGN_REQUEST", "HANDOFF_TO_PERSON"] + [f"REMINDER_{i}" for i in range(1, len(CFG["reminder_days"]) + 1)])
        for types in per.values():
            self.assertEqual(sorted(types), expected)

    def test_schedule_dates_follow_config(self):
        from datetime import timedelta
        d0 = date(2026, 1, 2)  # TCK-1002 opened
        for i, dd in enumerate(CFG["reminder_days"], 1):
            r = next(e for e in self.box if e["ticket"] == "TCK-1002" and e["type"] == f"REMINDER_{i}")
            self.assertEqual(r["date"], (d0 + timedelta(days=dd)).isoformat())
        h = next(e for e in self.box if e["ticket"] == "TCK-1002" and e["type"] == "HANDOFF_TO_PERSON")
        self.assertEqual(h["date"], (d0 + timedelta(days=CFG["escalate_after_days"])).isoformat())

    def test_current_cadence_is_3_7_handoff_14(self):
        self.assertEqual((CFG["reminder_days"], CFG["escalate_after_days"]), ([3, 7], 14))
        h = next(e for e in self.box if e["ticket"] == "TCK-1002" and e["type"] == "HANDOFF_TO_PERSON")
        self.assertEqual(h["date"], "2026-01-16")

    def test_after_lower_and_reported(self):
        self.assertLess(self.s["after_minutes"], self.s["before_minutes"])
        rep = (self.out / "report.md").read_text(encoding="utf-8")
        for must in ("Before → after", "Sensitivity", "Break-even", "Data quality"):
            self.assertIn(must, rep)

    def test_replay_covers_every_day(self):
        days = read_csv(self.out / "replay_by_day.csv")
        self.assertEqual(days[0]["date"], "2026-01-02")
        self.assertEqual(sum(int(d["esign_requests"]) for d in days), 36)


class Behaviour(unittest.TestCase):
    def test_idempotent(self):
        a, b = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
        tc.run(TICKETS, CFG, a)
        tc.run(TICKETS, CFG, b)
        for f in ("tracker.csv", "outbox.jsonl", "replay_by_day.csv", "summary.json", "report.md"):
            self.assertTrue(filecmp.cmp(a / f, b / f, shallow=False), f)

    def test_as_of_chase_list(self):
        out = Path(tempfile.mkdtemp())
        tc.run(TICKETS, CFG, out, as_of=date(2026, 1, 5))
        due = read_csv(out / "chase_list_2026-01-05.csv")
        self.assertIn("TF-TCK-1002", {d["request_id"] for d in due})  # opened Jan 2 → first reminder Jan 5

    def test_dirty_utf16_input_quarantined_rest_processed(self):
        d = Path(tempfile.mkdtemp())
        f = d / "fresh.csv"
        body = (HEAD + "TCK-9001,2026-04-01,Tax form (W-9/W-8),creator_a,Ops Support,40,Open\n"
                "TCK-9001,2026-04-01,Tax form (W-9/W-8),creator_a,Ops Support,40,Open\n"      # duplicate
                "TCK-9002,2026-13-02,Tax form (W-9/W-8),creator_b,,30,Open\n"                 # bad date
                "TCK-9003,2026-04-02,Tax form (W-9/W-8),creator_c,Ops Support,abc,Open\n"     # bad minutes
                "TCK-9004,2026-04-03,Thumbnail re-upload,creator_d,Ops Support,20,Open\n")    # not tax → ignored
        f.write_bytes(body.encode("utf-16"))
        s = tc.run(f, CFG, d / "out")
        self.assertEqual((s["input_rows"], s["quarantined"], s["tax_form_tickets"]), (5, 3, 1))
        q = (d / "out" / "quarantine.csv").read_text(encoding="utf-8")
        for reason in ("duplicate Ticket_ID", "bad Date", "non-numeric Handle_Minutes"):
            self.assertIn(reason, q)

    def test_new_quarter_file_runs_unchanged(self):
        d = Path(tempfile.mkdtemp())
        f = d / "q2.csv"
        f.write_text(HEAD + "TCK-2001,2026-04-02,Tax form (W-9/W-8),creator_x,Ops Support,35,Closed\n"
                            "TCK-2002,2026-05-11,Tax form (W-9/W-8),creator_y,Ops Support,45,Open\n", encoding="utf-8")
        s = tc.run(f, CFG, d / "out")
        self.assertEqual((s["tax_form_tickets"], s["before_minutes"]), (2, 80))

    def test_no_tax_rows_fails_loudly(self):
        d = Path(tempfile.mkdtemp())
        f = d / "none.csv"
        f.write_text(HEAD + "TCK-1,2026-01-01,Login issue,c,Ops Support,10,Closed\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            tc.run(f, CFG, d / "out")


if __name__ == "__main__":
    unittest.main()
