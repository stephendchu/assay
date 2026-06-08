from assay.faithfulness import faithfulness


def _supported(_prompt):
    return "SUPPORTED\nThe evidence states the figure directly."


def _unsupported(_prompt):
    return "UNSUPPORTED\nThe figure is not in the evidence."


def test_entailed_claim_scores_1():
    s = faithfulness(
        "R&D expense was $34,550M",
        "Research and development expense was $34,550 million.",
        judge=_supported,
    )
    assert s.value == 1.0 and s.reason


def test_unsupported_claim_scores_0():
    s = faithfulness(
        "iPhone unit sales fell 8%",
        "Research and development expense was $34,550 million.",
        judge=_unsupported,
    )
    assert s.value == 0.0


def test_blank_or_garbage_judge_is_unsupported():
    # A claim only ships on an explicit SUPPORTED — fail closed.
    assert faithfulness("anything", "anything", judge=lambda _p: "").value == 0.0
    assert faithfulness("anything", "anything", judge=lambda _p: "maybe?").value == 0.0
