from assay.review import review_queue


def test_blocks_and_abstentions_always_reviewed():
    items = [{"id": "a", "verdict": "block"}, {"id": "b", "verdict": "review"},
             {"id": "c", "verdict": "approve"}, {"id": "d", "verdict": "approve"}]
    q = review_queue(items, sample_rate=0.0)
    ids = {r["id"] for r in q["queue"]}
    assert {"a", "b"} <= ids and q["full_review"] == 2
    assert q["approvals_sampled"] == 0          # rate 0 -> only the risky ones go to a human


def test_approvals_sampled_deterministically():
    items = [{"id": str(i), "verdict": "approve"} for i in range(10)]
    q1 = review_queue(items, sample_rate=0.3, seed=1)
    q2 = review_queue(items, sample_rate=0.3, seed=1)
    assert q1["approvals_sampled"] == 3
    assert [r["id"] for r in q1["queue"]] == [r["id"] for r in q2["queue"]]
