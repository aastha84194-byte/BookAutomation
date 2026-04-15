"""
AI Engine Module
================
Integrates the Google Gemini API for book intelligence features:
  - Summary generation
  - Genre classification
  - Sentiment analysis
  - Recommendation logic ("If you like X, try Y")

Caching Strategy:
  All prompts are hashed (MD5) and responses cached in Redis via Django's
  cache framework. Cache TTL defaults to 24 hours (AI_CACHE_TTL setting).
"""

import hashlib
import logging

import google.generativeai as genai
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def _cache_key(prompt: str) -> str:
    """Return a Redis-safe cache key from an MD5 hash of the prompt."""
    return f"ai_resp_{hashlib.md5(prompt.encode('utf-8')).hexdigest()}"


def _get_model() -> genai.GenerativeModel:
    """Initialise and return the Gemini generation model."""
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(settings.GEMINI_MODEL)


# ---------------------------------------------------------------
# Core Cached Generation
# ---------------------------------------------------------------
def cached_generate(prompt: str, ttl: int = None) -> str | None:
    """
    Send a prompt to Gemini and cache the response.

    Flow:
      1. Hash the prompt → Redis cache key.
      2. Return cached value if it exists (cache HIT).
      3. Otherwise call the Gemini API, store the result, and return it.

    Args:
        prompt: The full text prompt to send.
        ttl:    Cache TTL in seconds. Defaults to settings.AI_CACHE_TTL (24 h).

    Returns:
        Generated text string, or None on API failure.
    """
    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is not configured — AI features disabled.")
        return None

    if ttl is None:
        ttl = getattr(settings, "AI_CACHE_TTL", 86400)

    key = _cache_key(prompt)

    # ── Cache HIT ─────────────────────────────────────────────────
    cached = cache.get(key)
    if cached is not None:
        logger.debug(f"AI cache HIT for key {key[:16]}…")
        return cached

    # ── Cache MISS → API call ──────────────────────────────────────
    try:
        model = _get_model()
        response = model.generate_content(prompt)
        result = response.text.strip()
        cache.set(key, result, timeout=ttl)
        logger.debug(f"AI cache MISS → stored result (key {key[:16]}…, TTL {ttl}s)")
        return result
    except Exception as exc:
        logger.error(f"Gemini API call failed: {exc}")
        return None


# ---------------------------------------------------------------
# Feature Functions
# ---------------------------------------------------------------
def generate_summary(title: str, description: str, genre: str = "") -> str:
    """
    Generate a concise 2–3 sentence reader-friendly summary of a book.

    Args:
        title:       Book title.
        description: Raw book description/blurb.
        genre:       Genre label (optional, improves context).

    Returns:
        AI-generated summary string.
    """
    if not description:
        fallback = f"A {genre} book" if genre else "A book"
        return f"{fallback} titled '{title}'."

    prompt = (
        f"You are a professional book critic. Write a compelling 2–3 sentence summary "
        f"of the following book that would entice a reader.\n\n"
        f"Title: {title}\n"
        f"Genre: {genre or 'Unknown'}\n"
        f"Description: {description}\n\n"
        f"Summary (2–3 sentences only):"
    )

    result = cached_generate(prompt)
    return result or f"A {genre or 'general'} book titled '{title}'."


def classify_genre(title: str, description: str) -> str:
    """
    Predict the genre of a book from its title and description.

    Returns one of the predefined genre labels.
    """
    if not description:
        return "General Fiction"

    allowed_genres = (
        "Fiction, Non-Fiction, Mystery, Thriller, Romance, Science Fiction, "
        "Fantasy, Historical Fiction, Biography, Self-Help, Horror, Adventure, "
        "Children's, Young Adult, Poetry, Philosophy, Business, Science, "
        "Travel, Humor, Literary Fiction, Classics"
    )

    prompt = (
        f"Classify the genre of this book. Choose EXACTLY ONE from: {allowed_genres}.\n\n"
        f"Title: {title}\n"
        f"Description: {description}\n\n"
        f"Genre (one word or short phrase only):"
    )

    result = cached_generate(prompt)
    if result:
        # Extract only the first line in case the model adds explanation
        return result.split("\n")[0].strip().rstrip(".")
    return "General Fiction"


def analyze_sentiment(title: str, description: str) -> str:
    """
    Analyze the emotional tone of a book based on its description.

    Returns a single-word tone label.
    """
    if not description:
        return "Neutral"

    prompt = (
        f"Determine the emotional tone of this book's description. "
        f"Choose EXACTLY ONE from: Uplifting, Dark, Neutral, Suspenseful, "
        f"Romantic, Humorous, Inspirational, Melancholic, Adventurous, Thought-provoking.\n\n"
        f"Title: {title}\n"
        f"Description: {description}\n\n"
        f"Tone (one word only):"
    )

    result = cached_generate(prompt)
    if result:
        return result.split("\n")[0].strip().rstrip(".")
    return "Neutral"


def generate_recommendations(
    target_title: str,
    target_description: str,
    all_books: list[dict],
) -> list[str]:
    """
    "If you like X, you'll like Y" recommendation logic.

    Uses Gemini to find thematically similar books from a candidate pool.

    Args:
        target_title:       Title of the reference book.
        target_description: Description of the reference book.
        all_books:          List of {'title': ..., 'description': ...} dicts.

    Returns:
        List of up to 5 recommended book titles.
    """
    if not all_books:
        return []

    # Limit candidate pool to avoid token overflow; sample up to 60 books
    candidates = all_books[:60]
    book_list = "\n".join(
        f"- {b['title']}: {(b.get('description') or '')[:120]}..."
        for b in candidates
    )

    prompt = (
        f'Based on the target book below, select 3–5 books from the list that '
        f'readers would also enjoy. Explain why each is similar.\n\n'
        f'Target Book: "{target_title}"\n'
        f"Description: {(target_description or '')[:400]}\n\n"
        f"Available Books:\n{book_list}\n\n"
        f"List ONLY the book titles (one per line, no numbering or bullet points):\n"
    )

    result = cached_generate(prompt, ttl=3600)  # Cache recommendations for 1 hour
    if result:
        lines = [
            line.strip().lstrip("-").strip() for line in result.split("\n")
        ]
        return [ln for ln in lines if ln and len(ln) > 2][:5]
    return []


# ---------------------------------------------------------------
# Convenience: All Insights in One Call
# ---------------------------------------------------------------
def generate_book_insights(book_data: dict, all_books: list[dict] = None) -> dict:
    """
    Generate all AI insights for a book in a single coordinated call.

    Args:
        book_data:  Dict with 'title', 'description', 'genre'.
        all_books:  Optional list of other books (for recommendations).

    Returns:
        Dict with keys: summary, genre, sentiment, recommendations.
    """
    title = book_data.get("title", "")
    description = book_data.get("description", "")
    genre = book_data.get("genre", "")

    logger.info(f"Generating AI insights for: '{title}'")

    summary = generate_summary(title, description, genre)
    classified_genre = classify_genre(title, description) if not genre else genre
    sentiment = analyze_sentiment(title, description)
    recommendations = []

    if all_books:
        recommendations = generate_recommendations(title, description, all_books)

    return {
        "summary": summary,
        "genre": classified_genre,
        "sentiment": sentiment,
        "recommendations": recommendations,
    }
