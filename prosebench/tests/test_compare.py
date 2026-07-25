from prosebench.document import NumberedDocument
from prosebench.pipeline import compare_documents


def test_compare_documents_returns_diff_and_metric_deltas() -> None:
    before = NumberedDocument.from_text("before.md", "One sentence.")
    after = NumberedDocument.from_text("after.md", "One sentence. A second sentence.")
    result = compare_documents(before, after)
    assert result.sentence_count_delta == 1
    assert "--- before.md" in result.unified_diff
    assert "+++ after.md" in result.unified_diff
