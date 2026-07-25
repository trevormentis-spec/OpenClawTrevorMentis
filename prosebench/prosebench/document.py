from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from pathlib import Path

from prosebench.models import DocumentStats

_WORD_RE = re.compile(r"\b[\w’'-]+\b", re.UNICODE)
_SENTENCE_RE = re.compile(r"(?<=[.!?])(?:[\"'”’)]*)\s+(?=[A-Z0-9\"'“‘(])")


@dataclass(frozen=True)
class Paragraph:
    number: int
    text: str

    @property
    def location(self) -> str:
        return f"P{self.number}"


@dataclass(frozen=True)
class NumberedDocument:
    name: str
    text: str
    paragraphs: tuple[Paragraph, ...]

    @classmethod
    def from_path(cls, path: Path) -> "NumberedDocument":
        if path.suffix.lower() not in {".md", ".markdown", ".txt"}:
            raise ValueError("The MVP accepts Markdown and plain text files only.")
        return cls.from_text(path.name, path.read_text(encoding="utf-8"))

    @classmethod
    def from_text(cls, name: str, text: str) -> "NumberedDocument":
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        blocks = [part.strip() for part in re.split(r"\n\s*\n", normalized) if part.strip()]
        if not blocks:
            raise ValueError("The document contains no prose to assess.")
        paragraphs = tuple(Paragraph(index, value) for index, value in enumerate(blocks, 1))
        return cls(name=name, text=normalized, paragraphs=paragraphs)

    def numbered_text(self) -> str:
        return "\n\n".join(f"[{p.location}] {p.text}" for p in self.paragraphs)

    def excerpt(self, location: str, limit: int = 360) -> str:
        match = re.fullmatch(r"P(\d+)", location.strip())
        if not match:
            return ""
        number = int(match.group(1))
        paragraph = next((p for p in self.paragraphs if p.number == number), None)
        return shorten(paragraph.text, limit) if paragraph else ""

    def sentences(self) -> list[str]:
        sentences: list[str] = []
        for paragraph in self.paragraphs:
            if re.fullmatch(r"#{1,6}\s+.+", paragraph.text):
                continue
            sentences.extend(value.strip() for value in _SENTENCE_RE.split(paragraph.text) if value.strip())
        return sentences

    def stats(self) -> DocumentStats:
        sentences = self.sentences()
        lengths = [len(words_in(sentence)) for sentence in sentences if words_in(sentence)]
        openings: dict[str, int] = {}
        for paragraph in self.paragraphs:
            tokens = words_in(re.sub(r"^#{1,6}\s*", "", paragraph.text))
            opening = " ".join(token.lower() for token in tokens[:3])
            if opening:
                openings[opening] = openings.get(opening, 0) + 1
        repeated = sorted(value for value, count in openings.items() if count > 1)
        if lengths:
            mean = statistics.fmean(lengths)
            stdev = statistics.pstdev(lengths) if len(lengths) > 1 else 0.0
            shortest, longest = min(lengths), max(lengths)
        else:
            mean = stdev = 0.0
            shortest = longest = 0
        text = self.text
        return DocumentStats(
            word_count=len(words_in(text)),
            sentence_count=len(lengths),
            paragraph_count=len(self.paragraphs),
            average_sentence_words=round(mean, 2),
            sentence_length_stdev=round(stdev, 2),
            shortest_sentence_words=shortest,
            longest_sentence_words=longest,
            citation_count=len(re.findall(r"(?:\[[0-9]+\]|\([A-Z][^()]{0,80}\b(?:19|20)\d{2}[a-z]?\)|https?://\S+)", text)),
            quotation_count=len(re.findall(r"[\"“][^\"”\n]{3,}[\"”]", text)),
            number_count=len(re.findall(r"(?<!\w)[+-]?(?:\d+[\d,]*(?:\.\d+)?%?)(?!\w)", text)),
            first_person_count=len(re.findall(r"\b(?:I|me|my|mine|we|us|our|ours)\b", text, re.I)),
            repeated_paragraph_openings=repeated,
        )


def words_in(text: str) -> list[str]:
    return _WORD_RE.findall(text)


def shorten(text: str, limit: int = 360) -> str:
    flat = re.sub(r"\s+", " ", text).strip()
    return flat if len(flat) <= limit else flat[: limit - 1].rstrip() + "…"
