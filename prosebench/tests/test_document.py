from prosebench.document import NumberedDocument


def test_document_numbering_and_metrics() -> None:
    document = NumberedDocument.from_text(
        "sample.md",
        "First sentence. Another one.\n\nSecond paragraph has 42 examples.",
    )
    assert [paragraph.location for paragraph in document.paragraphs] == ["P1", "P2"]
    assert "[P1]" in document.numbered_text()
    assert document.excerpt("P2").startswith("Second paragraph")
    stats = document.stats()
    assert stats.paragraph_count == 2
    assert stats.sentence_count == 3
    assert stats.number_count == 1
    assert stats.word_count > 5
