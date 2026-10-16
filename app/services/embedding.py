from collections.abc import Sequence
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.models.document_chunk import EMBEDDING_DIMENSIONS

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Load the sentence-transformers model."""
    model = SentenceTransformer(MODEL_NAME)
    dimensions = model.get_sentence_embedding_dimension()
    if dimensions != EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            f"{MODEL_NAME} produces {dimensions}-dim embeddings, but the "
            f"document_chunks.embedding column is {EMBEDDING_DIMENSIONS}-dim"
        )
    return model


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Embed a list of texts using the sentence-transformers model."""
    if not texts:
        return []
    model = _get_model()
    embeddings = model.encode(
        list(texts),
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return embeddings.tolist()


def embed_text(text: str) -> list[float]:
    """Embed a single text, e.g. a search query."""
    return embed_texts([text])[0]
