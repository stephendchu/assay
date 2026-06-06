"""Synthetic ITGC change-management control catalog + sample change records.

PUBLIC / SYNTHETIC ONLY — generic COSO/ITGC control language and made-up tickets.
Never any employer control, ticket, or audit data.
"""

CONTROLS = {
    "ITGC-CM-01": "All changes to production systems supporting financial reporting "
    "must be authorized via an approved change request prior to deployment.",
    "ITGC-CM-02": "Changes must be approved by someone independent of the developer "
    "(segregation of duties).",
    "ITGC-CM-03": "Changes must be tested and the results documented before promotion "
    "to production.",
}

# Clean change: every control assertion is grounded in the attached evidence.
CLEAN_CHANGE = {
    "id": "CHG-1042",
    "system": "billing-engine",
    "in_scope": True,
    "summary": "Adjust invoice rounding in the production billing pipeline.",
    "author": "m.chu",
    "evidence": {
        "approval": "Change CHG-1042 approved by j.lee on 2026-03-04, prior to deployment.",
        "approver": "j.lee",
        "test_signoff": "Unit and regression tests passed; results attached 2026-03-03.",
        "deployed_at": "2026-03-05",
    },
}

# Fabricated: the record asserts an approval that ISN'T in the evidence, so the
# agent's citation can't be grounded -> the gate BLOCKS it (anti-fabrication).
FABRICATED_CHANGE = {
    "id": "CHG-1099",
    "system": "billing-engine",
    "in_scope": True,
    "summary": "Hotfix tax calculation in production.",
    "author": "m.chu",
    "evidence": {
        "test_signoff": "Smoke test passed.",
        "deployed_at": "2026-03-06",
    },
}

# Self-approved: grounded, but the evidence reveals a control FAILURE (the
# approver is the developer) -> a recorded SoD deficiency in the workpaper.
SELF_APPROVED_CHANGE = {
    "id": "CHG-1101",
    "system": "billing-engine",
    "in_scope": True,
    "summary": "Change discount logic in production billing.",
    "author": "m.chu",
    "evidence": {
        "approval": "Change CHG-1101 approved by m.chu on 2026-03-07 prior to deployment.",
        "approver": "m.chu",
        "test_signoff": "Regression tests passed 2026-03-06.",
        "deployed_at": "2026-03-08",
    },
}
