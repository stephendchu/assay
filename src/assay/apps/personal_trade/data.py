"""Synthetic PAD data — PUBLIC / SYNTHETIC ONLY (no real names, accounts, or trades).

In reality the evidence arrives in many formats: a brokerage statement (CSV/PDF), Legal
pre-approval emails, a blackout list from a 3rd-party feed (JSON/XML), an HR covered-
accounts table. An **adapter layer** normalizes each into the text the analyst reads;
here we inline normalized text to keep the demo dependency-free.
"""

BLACKOUT = {"ACME": ("2026-03-01", "2026-03-31")}      # symbol -> (start, end) ISO dates
COVERED_ACCOUNTS = {"acct-100", "acct-fam"}            # employee + family / beneficially-owned


def _trade(id, account, symbol, trade_date, preapproval, statement=""):
    ev = {"legal_preapproval_email": preapproval}
    if statement:
        ev["brokerage_statement"] = statement
    return {"id": id, "employee": "u.chu", "account": account, "symbol": symbol,
            "side": "buy", "trade_date": trade_date, "evidence": ev}


CLEAN = _trade("TRD-001", "acct-100", "WIDGET", "2026-03-05",
    "Pre-clearance APPROVED for u.chu to BUY WIDGET, valid 2026-03-04 to 2026-03-06. — Legal",
    statement="Brokerage: BUY 100 WIDGET executed 2026-03-05 in acct-100.")
NO_APPROVAL = _trade("TRD-002", "acct-100", "GADGET", "2026-03-06",
    "[no pre-clearance on file]")
LATE_APPROVAL = _trade("TRD-003", "acct-100", "SPROCKET", "2026-03-05",
    "Pre-clearance APPROVED for u.chu to BUY SPROCKET on 2026-03-08. — Legal")
BLACKOUT_TRADE = _trade("TRD-004", "acct-100", "ACME", "2026-03-10",
    "Pre-clearance APPROVED for u.chu to BUY ACME, valid 2026-03-09 to 2026-03-11. — Legal")
AMBIGUOUS = _trade("TRD-005", "acct-fam", "COG", "2026-03-12",
    "Email — u.chu: 'hey is it ok if I pick up some COG?'  Jamie: 'yeah sounds fine, go ahead'")

ALL = [CLEAN, NO_APPROVAL, LATE_APPROVAL, BLACKOUT_TRADE, AMBIGUOUS]
