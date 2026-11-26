from search import rrf_merge


def row(chunk_id):
    """A fake search result: (chunk_id, source, pages, text, score)."""
    return (chunk_id, "file.pdf", [1], "some text", 0.0)


def test_chunk_found_by_both_lists_wins():
    vector = [row("A"), row("B"), row("C")]     # C is only 3rd here...
    keyword = [row("C"), row("D")]              # ...but 1st here
    merged = rrf_merge([vector, keyword])
    assert merged[0][0] == "C"                  # found by both → wins overall


def test_points_are_reciprocal_rank():
    merged = rrf_merge([[row("A")]], k=60)
    assert abs(merged[0][4] - 1 / 61) < 1e-9    # rank 1 → 1/(60+1)


def test_empty_lists():
    assert rrf_merge([[], []]) == []