"""
RAG Pipeline Module (PostgreSQL Vector Search)
==============================================
Implements Retrieval-Augmented Generation using pgvector on Neon.

Flow:
  1. Similarity search using Cosine Distance in PostgreSQL.
  2. Build context from retrieved chunks.
  3. Call Gemini LLM with context + question.
  4. Return answer with source citations.
"""

import hashlib
import logging
from typing import Any, List

import google.generativeai as genai
from django.conf import settings
from django.core.cache import cache
from pgvector.django import CosineDistance

from .models import BookChunk

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Embedding Generation
# ---------------------------------------------------------------
def get_embedding(text: str, task_type: str = "retrieval_document") -> List[float] | None:
    """
    Generate a Gemini embedding vector (768-dim) for `text`.
    Results are cached in Redis for 7 days.
    """
    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set — embeddings disabled.")
        return None

    cache_key = f"emb_{task_type}_{hashlib.md5(text.encode()).hexdigest()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        result = genai.embed_content(
            model=settings.GEMINI_EMBEDDING_MODEL,
            content=text,
            task_type=task_type,
        )
        embedding = result["embedding"]
        cache.set(cache_key, embedding, timeout=60 * 60 * 24 * 7)  # 7 days
        return embedding
    except Exception as exc:
        logger.error(f"Embedding generation failed: {exc}")
        return None


# ---------------------------------------------------------------
# Similarity Search (pgvector)
# ---------------------------------------------------------------
def similarity_search(query: str, top_k: int = 5) -> List[dict]:
    """
    Embed `query` and retrieve top-k chunks from PostgreSQL using CosineDistance.
    """
    query_embedding = get_embedding(query, task_type="retrieval_query")
    if query_embedding is None:
        return []

    # Query using pgvector's CosineDistance
    results = (
        BookChunk.objects.annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")
        .select_related("book")[:top_k]
    )

    formatted = []
    for chunk in results:
        formatted.append({
            "chunk_text": chunk.chunk_text,
            "book_id": str(chunk.book.id),
            "book_title": chunk.book.title,
            "chunk_index": chunk.chunk_index,
            "relevance_score": round(1.0 - float(chunk.distance), 3) if chunk.distance is not None else 0,
        })

    logger.info(f"RAG search '{query[:50]}...' -> found {len(formatted)} chunks")
    return formatted


# ---------------------------------------------------------------
# Full RAG Query
# ---------------------------------------------------------------
def rag_query(question: str, top_k: int = 5) -> dict:
    """
    Complete RAG workflow: Retrieve → Context → LLM.
    Cached in Redis for 1 hour.
    """
    cache_key = f"rag_{hashlib.md5(question.encode()).hexdigest()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    # 1. Retrieve
    search_results = similarity_search(question, top_k=top_k)
    if not search_results:
        return {
            "answer": "I don't have enough book data to answer that. Please ensure books are scraped and processed.",
            "sources": [],
            "context_used": "",
        }

    # 2. Build Context
    context_parts = []
    for i, r in enumerate(search_results, 1):
        context_parts.append(f"[Source {i} — {r['book_title']}]\n{r['chunk_text']}")
    context = "\n\n".join(context_parts)

    # 3. Generate Answer
    prompt = (
        "You are an AI book assistant. Answer using ONLY the context below.\n"
        "Cite books using [Book Title] notation. If answer is not present, say so.\n\n"
        f"--- CONTEXT ---\n{context}\n\n"
        f"QUESTION: {question}\n\n"
        "ANSWER:"
    )

    answer = "AI service unavailable."
    if settings.GEMINI_API_KEY:
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            response = model.generate_content(prompt)
            answer = response.text.strip()
        except Exception as exc:
            logger.error(f"RAG LLM failed: {exc}")
            answer = f"Error: {exc}"

    result = {
        "answer": answer,
        "sources": search_results,
        "context_used": context,
    }

    cache.set(cache_key, result, timeout=3600)
    return result
