"""Implement fixed-size and structure-aware chunking."""
import re
from .models import Chunk, DocumentPage


def fixed_size(page: DocumentPage, size: int = 500, overlap: int = 50) -> list[Chunk]:
    """Split text into overlapping windows and retain page metadata.
    
    Default: size=500, overlap=50 (step=450).
    """
    text = page.text
    if not text:
        return []

    chunks: list[Chunk] = []
    step = max(1, size - overlap)
    chunk_index = 0
    text_len = len(text)

    for start in range(0, text_len, step):
        end = min(text_len, start + size)
        chunk_text = text[start:end].strip()
        if not chunk_text:
            continue

        chunk_id = f"{page.document_id}_p{page.page:03d}_fixed_{chunk_index:03d}"
        chunk_meta = dict(page.metadata)
        chunk_meta.update({
            "chunk_type": "fixed_size",
            "chunk_index": chunk_index,
            "start_char": start,
            "end_char": end,
            "char_count": len(chunk_text)
        })

        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                document_id=page.document_id,
                source=page.source,
                page=page.page,
                text=chunk_text,
                metadata=chunk_meta
            )
        )
        chunk_index += 1
        if end >= text_len:
            break

    return chunks


def _split_oversized_paragraph(para: str, max_size: int) -> list[str]:
    """Split a single paragraph that exceeds max_size at sentence boundaries."""
    sentences = re.split(r"(?<=[.!?])\s+", para)
    sub_chunks: list[str] = []
    curr = ""
    for s in sentences:
        if not curr:
            curr = s
        elif len(curr) + 1 + len(s) <= max_size:
            curr += " " + s
        else:
            sub_chunks.append(curr.strip())
            curr = s
    if curr.strip():
        sub_chunks.append(curr.strip())
    # If any single sentence is still larger than max_size, hard-split it
    final_chunks: list[str] = []
    for c in sub_chunks:
        if len(c) <= max_size:
            final_chunks.append(c)
        else:
            for i in range(0, len(c), max_size):
                final_chunks.append(c[i:i + max_size].strip())
    return [c for c in final_chunks if c]


def by_paragraph(page: DocumentPage, max_size: int = 800) -> list[Chunk]:
    """Group paragraphs, split oversized paragraphs and retain metadata.
    
    Preserves semantic boundaries and coherent paragraph context.
    """
    text = page.text
    if not text:
        return []

    # Split into raw paragraphs by double newline
    raw_paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not raw_paras:
        raw_paras = [text]

    # Normalize list of candidate units (splitting units larger than max_size)
    atomic_units: list[str] = []
    for p in raw_paras:
        if len(p) <= max_size:
            atomic_units.append(p)
        else:
            atomic_units.extend(_split_oversized_paragraph(p, max_size))

    # Group adjacent units up to max_size
    grouped_texts: list[str] = []
    current_group: list[str] = []
    current_length = 0

    for unit in atomic_units:
        unit_len = len(unit)
        if not current_group:
            current_group.append(unit)
            current_length = unit_len
        elif current_length + 2 + unit_len <= max_size:
            current_group.append(unit)
            current_length += 2 + unit_len
        else:
            grouped_texts.append("\n\n".join(current_group))
            current_group = [unit]
            current_length = unit_len

    if current_group:
        grouped_texts.append("\n\n".join(current_group))

    chunks: list[Chunk] = []
    for chunk_index, chunk_text in enumerate(grouped_texts):
        chunk_text = chunk_text.strip()
        if not chunk_text:
            continue

        chunk_id = f"{page.document_id}_p{page.page:03d}_para_{chunk_index:03d}"
        chunk_meta = dict(page.metadata)
        chunk_meta.update({
            "chunk_type": "paragraph",
            "chunk_index": chunk_index,
            "char_count": len(chunk_text)
        })

        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                document_id=page.document_id,
                source=page.source,
                page=page.page,
                text=chunk_text,
                metadata=chunk_meta
            )
        )

    return chunks
