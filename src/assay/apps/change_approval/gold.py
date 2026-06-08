"""Synthetic, human-verifiable gold set for the change-approval eval.

PUBLIC / SYNTHETIC ONLY. Starter set — expand via the AI-draft -> human-verify
workflow in docs/VALIDATION.md. Each case labels the controls the evidence
*grounds*, any seeded deficiency, and whether the gate should block.
"""
from assay.apps.change_approval.controls import (
    CLEAN_CHANGE,
    FABRICATED_CHANGE,
    SELF_APPROVED_CHANGE,
)

MISSING_TEST_CHANGE = {
    "id": "CHG-1077", "system": "billing-engine", "in_scope": True,
    "summary": "Update late-fee calculation in production billing.",
    "author": "m.chu",
    "evidence": {
        "approval": "Change CHG-1077 approved by k.rao on 2026-03-10, prior to deployment.",
        "approver": "k.rao",
        "deployed_at": "2026-03-11",
    },
}

SECOND_CLEAN_CHANGE = {
    "id": "CHG-1120", "system": "ledger-poster", "in_scope": True,
    "summary": "Fix GL account mapping in the production ledger poster.",
    "author": "p.diaz",
    "evidence": {
        "approval": "Change CHG-1120 approved by s.kim on 2026-04-02, before release.",
        "approver": "s.kim",
        "test_signoff": "Full regression suite passed; evidence attached 2026-04-01.",
        "deployed_at": "2026-04-03",
    },
}

# controls = those the evidence grounds; deficiencies = seeded control failures.
GOLD = [
    {"change": CLEAN_CHANGE,         "controls": {"ITGC-CM-01", "ITGC-CM-03"}, "deficiencies": set(),          "expect_block": False},
    {"change": SECOND_CLEAN_CHANGE,  "controls": {"ITGC-CM-01", "ITGC-CM-03"}, "deficiencies": set(),          "expect_block": False},
    {"change": SELF_APPROVED_CHANGE, "controls": {"ITGC-CM-01", "ITGC-CM-03"}, "deficiencies": {"ITGC-CM-02"}, "expect_block": False},
    {"change": MISSING_TEST_CHANGE,  "controls": {"ITGC-CM-01"},               "deficiencies": set(),          "expect_block": False},
    {"change": FABRICATED_CHANGE,    "controls": {"ITGC-CM-03"},               "deficiencies": set(),          "expect_block": False},
]
