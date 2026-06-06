from assay.gate import Claim, Verdict, evaluate

SOURCE = "The board approved the merger on March 4. Revenue rose 12 percent."


def test_all_grounded_approves():
    d = evaluate(
        [
            Claim("merger approved", "The board approved the merger on March 4"),
            Claim("revenue up", "Revenue rose 12 percent"),
        ],
        SOURCE,
    )
    assert d.verdict is Verdict.APPROVE
    assert d.ungrounded == 0 and d.grounded == 2


def test_any_ungrounded_blocks_by_default():
    d = evaluate(
        [
            Claim("merger approved", "The board approved the merger on March 4"),
            Claim("fabricated", "The CEO resigned in April"),  # not in source
        ],
        SOURCE,
    )
    assert d.verdict is Verdict.BLOCK
    assert d.ungrounded == 1
    assert d.reasons  # the audit trail explains what failed


def test_ungrounded_routes_to_review_when_not_blocking():
    d = evaluate(
        [Claim("fabricated", "The CEO resigned in April")],
        SOURCE,
        block_if_any_ungrounded=False,
    )
    assert d.verdict is Verdict.REVIEW
