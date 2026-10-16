import asyncio

import pymupdf

from app.core import storage


class ExtractionError(Exception):
    pass


def _extract_text(data: bytes, mime_type: str) -> str:
    try:
        doc = pymupdf.open(stream=data, filetype=mime_type)
    except pymupdf.FileDataError as e:
        raise ExtractionError(f"Could not open document as {mime_type}") from e

    with doc:
        if doc.needs_pass:
            raise ExtractionError("Document is password protected")
        pages = (page.get_text().strip() for page in doc)
        return "\n\n".join(page for page in pages if page)


async def extract_content(storage_key: str, mime_type: str) -> str:
    data = await storage.get_object(storage_key)
    return await asyncio.to_thread(_extract_text, data, mime_type)
