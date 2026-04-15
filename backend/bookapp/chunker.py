"""
Smart Chunking Module
======================
Splits book text into semantically coherent chunks for the RAG pipeline.

Strategies implemented:
  1. Semantic chunking — splits at sentence boundaries to preserve meaning.
  2. Overlapping windows — each chunk overlaps with the previous by `overlap`
     tokens to maintain context continuity across chunk boundaries.
  3. Word-level fallback — for very long single sentences.
"""

import logging
import re
from typing import List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Default Parameters
# ---------------------------------------------------------------
DEFAULT_CHUNK_SIZE = 500    # Target tokens per chunk
DEFAULT_OVERLAP = 100       # Overlap tokens between consecutive chunks
MIN_CHUNK_TOKENS = 10       # Discard chunks shorter than this (lowered for accessibility)


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def estimate_tokens(text: str) -> int:
    """Rough token count: 1 token ≈ 4 characters (suitable for English text)."""
    return max(1, len(text) // 4)


def split_sentences(text: str) -> List[str]:
    """
    Split text into sentences using punctuation-aware regex.
    Handles abbreviations and ellipses reasonably well.
    """
    # Split on . ! ? followed by whitespace + uppercase (sentence boundary)
    raw = re.split(r"(?<=[.!?])\s+(?=[A-Z\"\'])", text.strip())
    return [s.strip() for s in raw if s.strip()]


def _overlap_tail(sentences: List[str], overlap_tokens: int) -> List[str]:
    """
    Return trailing sentences from `sentences` that fit within `overlap_tokens`.
    Used to prepend context from the previous chunk into the next one.
    """
    tail = []
    count = 0
    for sent in reversed(sentences):
        toks = estimate_tokens(sent)
        if count + toks <= overlap_tokens:
            tail.insert(0, sent)
            count += toks
        else:
            break
    return tail


def _chunk_by_words(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Fallback chunker: splits by word count for very long single sentences.
    Applies an overlapping sliding window.
    """
    words = text.split()
    step = max(1, chunk_size - overlap)
    chunks = []
    for i in range(0, len(words), step):
        piece = " ".join(words[i : i + chunk_size])
        if piece:
            chunks.append(piece)
    return chunks


# ---------------------------------------------------------------
# Core Chunking
# ---------------------------------------------------------------
def semantic_chunk(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> List[str]:
    """
    Semantic chunking with overlapping windows.

    Algorithm:
      1. Split text into sentences.
      2. Accumulate sentences until the chunk reaches `chunk_size` tokens.
      3. When the budget is exceeded, close the chunk and start a new one,
         carrying over a `overlap`-token tail for context continuity.
      4. Discard chunks shorter than MIN_CHUNK_TOKENS.

    Args:
        text:       Input text (book description, summary, etc.).
        chunk_size: Target tokens per chunk.
        overlap:    Overlap tokens between consecutive chunks.

    Returns:
        List of text chunk strings.
    """
    if not text or not text.strip():
        return []

    sentences = split_sentences(text)
    if not sentences:
        return [text.strip()] if estimate_tokens(text) >= MIN_CHUNK_TOKENS else []

    chunks: List[str] = []
    current_sents: List[str] = []
    current_tokens = 0

    for sent in sentences:
        sent_tokens = estimate_tokens(sent)

        # Very long single sentence → word-level fallback
        if sent_tokens > chunk_size and not current_sents:
            logger.debug(f"Long sentence ({sent_tokens} tokens) — using word chunker.")
            chunks.extend(_chunk_by_words(sent, chunk_size, overlap))
            continue

        # Flush current chunk when budget exceeded
        if current_tokens + sent_tokens > chunk_size and current_sents:
            chunk_text = " ".join(current_sents)
            if estimate_tokens(chunk_text) >= MIN_CHUNK_TOKENS:
                chunks.append(chunk_text)

            # Start next chunk with overlapping tail
            overlap_sents = _overlap_tail(current_sents, overlap)
            current_sents = overlap_sents
            current_tokens = sum(estimate_tokens(s) for s in current_sents)

        current_sents.append(sent)
        current_tokens += sent_tokens

    # Flush the final chunk
    if current_sents:
        chunk_text = " ".join(current_sents)
        if estimate_tokens(chunk_text) >= MIN_CHUNK_TOKENS:
            chunks.append(chunk_text)

    logger.debug(f"Chunked {estimate_tokens(text)} tokens → {len(chunks)} chunks")
    return chunks


# ---------------------------------------------------------------
# Book-Specific Chunking
# ---------------------------------------------------------------
def chunk_book_content(book: dict) -> List[str]:
    """
    Build a rich multi-section text from a book's fields and chunk it.

    Sections created:
      1. Header   — title, author, genre, rating, price (always one chunk)
      2. Description — semantic chunks of description text
      3. Summary  — semantic chunks of AI-generated summary
      4. Insights — sentiment and genre classification (one chunk)

    Args:
        book: Dict with keys: title, author, description, genre,
              summary, sentiment, rating, price, etc.

    Returns:
        List of text chunks for embedding.
    """
    sections: List[str] = []

    # ── 1. Header chunk (book identity) ──────────────────────────
    header_lines = []
    if book.get("title"):
        header_lines.append(f"Book Title: {book['title']}")
    if book.get("author"):
        header_lines.append(f"Author: {book['author']}")
    if book.get("genre"):
        header_lines.append(f"Genre: {book['genre']}")
    if book.get("rating") is not None:
        header_lines.append(f"Rating: {book['rating']}/5.0")
    if book.get("price"):
        header_lines.append(f"Price: {book['price']}")
    if book.get("availability"):
        header_lines.append(f"Availability: {book['availability']}")
    if header_lines:
        sections.append("\n".join(header_lines))

    # ── 2. Description chunks ──────────────────────────────────────
    if book.get("description"):
        desc_text = f"Description: {book['description']}"
        sections.extend(semantic_chunk(desc_text))

    # ── 3. AI Summary chunks ───────────────────────────────────────
    if book.get("summary"):
        summary_text = f"Summary: {book['summary']}"
        sections.extend(semantic_chunk(summary_text))

    # ── 4. AI Insights chunk ───────────────────────────────────────
    insight_lines = []
    if book.get("sentiment"):
        insight_lines.append(f"Tone / Sentiment: {book['sentiment']}")
    if book.get("genre"):
        insight_lines.append(f"AI-Classified Genre: {book['genre']}")
    if insight_lines:
        sections.append("\n".join(insight_lines))

    # Filter out chunks that are too short to be useful
    valid = [c for c in sections if c and estimate_tokens(c) >= MIN_CHUNK_TOKENS]
    logger.debug(f"chunk_book_content: {len(valid)} valid chunks for '{book.get('title', '?')}'")
    return valid
