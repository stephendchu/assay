from assay.apps.change_approval.gold import GOLD
from assay.eval import bootstrap_ci, evaluate, f1, precision_recall


def test_precision_recall():
    assert precision_recall({"a", "b"}, {"a"}) == (0.5, 1.0)
    assert precision_recall(set(), set()) == (1.0, 1.0)
    assert precision_recall({"x"}, set()) == (0.0, 1.0)


def test_f1():
    assert f1(1.0, 1.0) == 1.0
    assert f1(0.0, 0.0) == 0.0
    assert round(f1(0.5, 1.0), 2) == 0.67


def test_bootstrap_ci_orders_bounds():
    pt, lo, hi = bootstrap_ci([1.0, 0.5, 0.75, 1.0])
    assert lo <= pt <= hi and 0.0 <= lo and hi <= 1.0


def test_deterministic_baseline_runs_and_scores():
    rep = evaluate(GOLD, use_llm=False)
    assert rep.n == len(GOLD)
    for metric in (rep.f1, rep.grounding_rate):
        assert 0.0 <= metric[1] <= metric[0] <= metric[2] <= 1.0
    assert 0.0 <= rep.deficiency_accuracy <= 1.0
    assert 0.0 <= rep.gate_accuracy <= 1.0
    # the naive baseline emits both controls regardless -> it over-blocks the
    # partial-evidence cases, so gate accuracy is provably imperfect. (This is the
    # honest finding the LLM mapper is meant to beat.)
    assert rep.gate_accuracy < 1.0
