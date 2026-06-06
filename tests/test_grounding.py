from assay.grounding import is_grounded

SOURCE = "Research and development expense was $34,550 million for fiscal 2025."


def test_exact_span_is_grounded():
    assert is_grounded("research and development expense was $34,550 million", SOURCE)


def test_whitespace_and_case_are_normalized():
    assert is_grounded("RESEARCH   and\nDevelopment Expense", SOURCE)


def test_absent_span_is_not_grounded():
    assert not is_grounded("operating income was $5 billion", SOURCE)


def test_too_short_citation_is_rejected():
    assert not is_grounded("was", SOURCE)  # a 3-char overlap proves nothing
