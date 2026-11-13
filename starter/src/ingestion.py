"""Read and normalize source data from PDF."""
import json
import re
import unicodedata
from pathlib import Path
import pypdf

from .models import DocumentPage


def normalize_text(text: str) -> str:
    """Normalize Unicode and whitespace without discarding useful structure."""
    if not text:
        return ""
    # Unicode normalization to NFC
    text = unicodedata.normalize("NFC", text)
    # Replace non-breaking spaces and carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    # Replace tabs with spaces
    text = text.replace("\t", " ")
    # Collapse multiple inline spaces while keeping newlines
    lines = [re.sub(r"[ ]{2,}", " ", line.strip()) for line in text.split("\n")]
    # Collapse more than 2 consecutive empty lines
    cleaned_text = "\n".join(lines)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
    return cleaned_text.strip()


def load_pdf(
    path: Path,
    document_id: str = "openstax-us-history",
    source: str = "starter/data/US_History_-_WEB.pdf",
    start_page: int = 23,
    end_page: int = 100,
    manifest_path: Path | None = None
) -> list[DocumentPage]:
    """Extract physical pages from PDF according to manifest or page range.
    
    Default range 23 to 100 selects the 78 content pages of Chapters 1-3,
    excluding pages 1-22 (cover, table of contents, preface).
    """
    if not path.exists():
        raise FileNotFoundError(f"PDF source not found at: {path}")

    # Load page-level metadata from manifest if provided/available
    manifest_metadata: dict[int, dict] = {}
    if manifest_path is None:
        candidate_manifest = path.parent / "manifest.json"
        if candidate_manifest.exists():
            manifest_path = candidate_manifest
        else:
            root_manifest = Path("data/manifest.json")
            if root_manifest.exists():
                manifest_path = root_manifest

    if manifest_path and manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
            for p_info in manifest_data.get("pages", []):
                manifest_metadata[p_info["physical_page"]] = p_info

    reader = pypdf.PdfReader(str(path))
    total_physical_pages = len(reader.pages)
    pages: list[DocumentPage] = []

    for physical_page in range(start_page, min(end_page + 1, total_physical_pages + 1)):
        page_idx = physical_page - 1
        raw_text = reader.pages[page_idx].extract_text() or ""
        cleaned = normalize_text(raw_text)

        # Retrieve metadata from manifest or assign defaults
        p_meta = manifest_metadata.get(physical_page, {})
        chapter = p_meta.get("chapter", "")
        section = p_meta.get("section", "")
        is_review = p_meta.get("is_review_question_page", False)
        book_page = p_meta.get("book_page", physical_page - 16)

        # Fallback chapter heuristic if manifest not found
        if not chapter:
            if physical_page <= 46:
                chapter = "Chapter 1: The Americas, Europe, and Africa Before 1492"
            elif physical_page <= 72:
                chapter = "Chapter 2: Early Globalization: The Atlantic World, 1492-1650"
            else:
                chapter = "Chapter 3: Creating New Social Orders: Colonial Societies, 1500-1700"

        metadata = {
            "book_page": book_page,
            "chapter": chapter,
            "section": section,
            "is_review_question_page": is_review,
            "raw_char_count": len(raw_text),
            "clean_char_count": len(cleaned),
            "is_empty": len(cleaned) == 0
        }

        pages.append(
            DocumentPage(
                document_id=document_id,
                source=source,
                page=physical_page,
                text=cleaned,
                metadata=metadata
            )
        )

    return pages
