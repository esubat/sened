import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


_SEPARATORS = [
    r"\n{2,}",
    r"(?<=[.!?])\s+",
    r"(?<=[;:])\s+",
    r"(?<=,)\s+",
    r"\s+",
    "",
]

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=_SEPARATORS,
    is_separator_regex=True,
    keep_separator="end",
    strip_whitespace=True,
)


def _normalize(text: str) -> str:
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Rejoin words hyphenated across a line wrap: "retrie-\nval" -> "retrieval".
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # Unwrap hard-wrapped lines while preserving paragraph breaks.
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t\f\v]+", " ", text)
    return text.strip()


def chunk_text(text: str) -> list[str]:
    """Split extracted document text into overlapping, sentence-aligned chunks."""
    chunks = text_splitter.split_text(_normalize(text))
    # Drop fragments with no words (page numbers, stray punctuation).
    return [chunk for chunk in chunks if re.search(r"\w{2,}", chunk)]
