"""
Celery Async Tasks
==================
Background jobs for:
  - Bulk web scraping (scrape_books_task)
  - Per-book AI processing + embedding (process_book_task)
  - Batch processing of all pending books (process_all_pending_books)
"""

import logging

from celery import shared_task
from django.db import transaction

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def scrape_books_task(self, max_pages: int = 5):
    """
    Celery task: Scrape books from books.toscrape.com and store in DB.

    After scraping, automatically triggers AI processing for new books.

    Args:
        max_pages: Number of catalogue pages to scrape (1–50).

    Returns:
        Dict with 'created', 'skipped', 'total', 'status'.
    """
    from .models import Book
    from .scraper import BookScraper

    logger.info(f"[TASK] scrape_books_task started — max_pages={max_pages}")

    try:
        # Run the Selenium scraper inside a context manager
        with BookScraper(headless=True) as scraper:
            books_data = scraper.scrape_all_books(max_pages=max_pages)

        created_count = 0
        skipped_count = 0

        # Use an atomic transaction for bulk inserts
        with transaction.atomic():
            for book_data in books_data:
                book_url = book_data.get("book_url", "")
                if not book_url:
                    continue

                # Idempotent: skip if already in DB
                if Book.objects.filter(book_url=book_url).exists():
                    skipped_count += 1
                    continue

                Book.objects.create(
                    title=book_data.get("title", "Unknown Title"),
                    author=book_data.get("author", "Unknown"),
                    rating=book_data.get("rating"),
                    num_reviews=book_data.get("num_reviews", 0),
                    description=book_data.get("description", ""),
                    book_url=book_url,
                    cover_image=book_data.get("cover_image", ""),
                    genre=book_data.get("genre", ""),
                    price=book_data.get("price", ""),
                    availability=book_data.get("availability", ""),
                    processed=False,
                )
                created_count += 1

        logger.info(
            f"[TASK] Scraping done — {created_count} new, {skipped_count} skipped"
        )

        # Queue AI processing for newly added books
        if created_count > 0:
            process_all_pending_books.delay()

        return {
            "status": "success",
            "created": created_count,
            "skipped": skipped_count,
            "total": len(books_data),
        }

    except Exception as exc:
        logger.error(f"[TASK] scrape_books_task failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def process_book_task(self, book_id: str):
    """
    Celery task: Generate AI insights and embeddings for a single book.

    Steps:
      1. Generate summary, genre, sentiment, recommendations via Gemini.
      2. Update the Book record with AI insights.
      3. Chunk the book content (semantic chunking).
      4. Embed chunks and upsert to ChromaDB.
      5. Save BookChunk records to PostgreSQL.

    Args:
        book_id: UUID string of the book to process.
    """
    from .ai_engine import generate_book_insights
    from .chunker import chunk_book_content
    from .models import Book, BookChunk
    from .rag import get_embedding

    logger.info(f"[TASK] process_book_task started for book_id={book_id}")

    try:
        book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        logger.error(f"[TASK] Book {book_id} not found in DB")
        return {"status": "error", "message": "Book not found"}

    try:
        # Get a sample of other books for recommendation context
        other_books = list(
            Book.objects.exclude(id=book_id)
            .values("title", "description")[:100]
        )

        # ── 1. AI Insights ─────────────────────────────────────────
        insights = generate_book_insights(
            {"title": book.title, "description": book.description, "genre": book.genre},
            all_books=other_books,
        )

        # ── 2. Persist insights ────────────────────────────────────
        book.summary = insights.get("summary", "")
        book.genre = insights.get("genre", book.genre)
        book.sentiment = insights.get("sentiment", "")
        book.recommendations = insights.get("recommendations", [])
        book.processed = True
        book.save()

        # ── 3. Smart Chunking ──────────────────────────────────────
        chunks = chunk_book_content(
            {
                "title": book.title,
                "author": book.author,
                "description": book.description,
                "genre": book.genre,
                "summary": book.summary,
                "sentiment": book.sentiment,
                "rating": str(book.rating) if book.rating is not None else "",
                "price": book.price,
                "availability": book.availability,
            }
        )

        # ── 4. Generate Embeddings & Save BookChunks ─────────────────
        BookChunk.objects.filter(book=book).delete()  # Clear stale chunks
        
        chunk_records = []
        for i, chunk_text in enumerate(chunks):
            embedding = get_embedding(chunk_text, task_type="retrieval_document")
            chunk_records.append(
                BookChunk(
                    book=book,
                    chunk_text=chunk_text,
                    chunk_index=i,
                    embedding=embedding,
                    embedding_id=f"{book_id}_chunk_{i}",
                )
            )
        
        if chunk_records:
            BookChunk.objects.bulk_create(chunk_records)

        logger.info(
            f"[TASK] '{book.title}' processed — {len(chunks)} chunks, "
            f"genre='{book.genre}', sentiment='{book.sentiment}'"
        )
        return {
            "status": "success",
            "book_id": book_id,
            "chunks_created": len(chunks),
            "genre": book.genre,
            "sentiment": book.sentiment,
        }

    except Exception as exc:
        logger.error(f"[TASK] process_book_task failed for {book_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task
def process_all_pending_books():
    """
    Celery task: Queue AI processing for all unprocessed books in the DB.
    Useful for batch-processing after a bulk scrape.
    """
    from .models import Book

    pending = Book.objects.filter(processed=False)
    count = pending.count()
    logger.info(f"[TASK] process_all_pending_books — queuing {count} books")

    for book in pending:
        process_book_task.delay(str(book.id))

    return {"queued": count}
