"""
REST API Views for BookAutomation
===================================
Endpoints:
  GET  /api/books/                        — List all books (paginated, filterable)
  GET  /api/books/<id>/                   — Book detail with AI insights
  GET  /api/books/<id>/recommendations/   — Related book recommendations
  POST /api/books/upload/                 — Manual book upload
  POST /api/books/scrape/                 — Trigger Selenium bulk scrape (async)
  POST /api/qa/                           — RAG question-answering
  GET  /api/chat/history/                 — Saved Q&A chat history
  GET  /api/genres/                       — List of all distinct genres
  GET  /api/stats/                        — Database statistics
"""

import logging

from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Book, ChatHistory
from .serializers import (
    BookDetailSerializer,
    BookListSerializer,
    BookUploadSerializer,
    ChatHistorySerializer,
    RAGQuerySerializer,
    ScrapeRequestSerializer,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------
class BookPagination(PageNumberPagination):
    """Standard paginator for book listing and chat history endpoints."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


# ---------------------------------------------------------------
# GET /api/books/
# ---------------------------------------------------------------
class BookListView(generics.ListAPIView):
    """
    List all books with optional filtering and search.

    Query Parameters:
      genre     — filter by genre name (case-insensitive partial match)
      search    — search title or author
      processed — 'true'/'false' to filter by processing status
      page      — page number (default 1)
      page_size — results per page (default 20, max 100)
    """

    serializer_class = BookListSerializer
    pagination_class = BookPagination

    def get_queryset(self):
        qs = Book.objects.all()

        # Genre filter
        genre = self.request.query_params.get("genre")
        if genre:
            qs = qs.filter(genre__icontains=genre)

        # Full-text search (title + author)
        search = self.request.query_params.get("search")
        if search:
            from django.db.models import Q
            qs = qs.filter(Q(title__icontains=search) | Q(author__icontains=search))

        # Processed filter
        processed = self.request.query_params.get("processed")
        if processed is not None:
            qs = qs.filter(processed=processed.lower() == "true")

        return qs.distinct()

    def list(self, request, *args, **kwargs):
        # Cache list responses for 5 minutes keyed by full URL
        cache_key = f"book_list:{request.get_full_path()}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=300)
        return response


# ---------------------------------------------------------------
# GET /api/books/<id>/
# ---------------------------------------------------------------
class BookDetailView(generics.RetrieveAPIView):
    """
    Retrieve all details for a specific book, including AI insights and chunks.
    """

    serializer_class = BookDetailSerializer
    queryset = Book.objects.prefetch_related("chunks")
    lookup_field = "id"


# ---------------------------------------------------------------
# GET /api/books/<id>/recommendations/
# ---------------------------------------------------------------
class BookRecommendationsView(APIView):
    """
    Return book recommendations based on a given book.

    Logic:
      1. Use the book's 'recommendations' field (AI-generated titles).
      2. Find matching Book records in the DB.
      3. Fallback: return top-rated books in the same genre.
    """

    def get(self, request, id):
        book = get_object_or_404(Book, id=id)

        cache_key = f"recommendations:{id}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        rec_titles = book.recommendations or []
        recommended_books = []

        # Try to match AI-suggested titles against the DB
        for title in rec_titles:
            match = Book.objects.filter(title__icontains=title[:25]).exclude(id=id).first()
            if match:
                recommended_books.append(match)

        # Fallback: top-rated books in the same genre
        if not recommended_books and book.genre:
            recommended_books = list(
                Book.objects.filter(genre__icontains=book.genre)
                .exclude(id=id)
                .order_by("-rating")[:6]
            )

        serializer = BookListSerializer(recommended_books, many=True)
        result = {
            "book_id": str(id),
            "book_title": book.title,
            "recommendations": serializer.data,
            "ai_suggestions": rec_titles,
        }

        cache.set(cache_key, result, timeout=3600)
        return Response(result)


# ---------------------------------------------------------------
# POST /api/books/upload/
# ---------------------------------------------------------------
class BookUploadView(APIView):
    """
    Manually add a book to the database and queue AI processing.

    Body: { title, author, rating, num_reviews, description, book_url,
            cover_image, genre }
    """

    def post(self, request):
        serializer = BookUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        book = serializer.save()

        # Queue async AI processing
        task_queued = False
        try:
            from .tasks import process_book_task
            process_book_task.delay(str(book.id))
            task_queued = True
        except Exception as exc:
            logger.warning(f"Could not queue Celery task: {exc}")

        # Invalidate cached list (best-effort)
        try:
            cache.delete_pattern("book_list:*")  # django-redis extension
        except AttributeError:
            pass  # Standard Redis backend doesn't support pattern delete

        return Response(
            {
                "message": "Book uploaded. AI processing queued.",
                "book_id": str(book.id),
                "task_queued": task_queued,
                "book": BookListSerializer(book).data,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------
# POST /api/books/scrape/
# ---------------------------------------------------------------
class ScrapeView(APIView):
    """
    Trigger a background Selenium scraping job.

    Body: { max_pages: int }  (1–50, default 5)
    Returns: 202 Accepted with task_id.
    """

    def post(self, request):
        serializer = ScrapeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        max_pages = serializer.validated_data.get("max_pages", 5)

        try:
            from .tasks import scrape_books_task
            task = scrape_books_task.delay(max_pages=max_pages)
            return Response(
                {
                    "message": f"Scraping {max_pages} page(s) started in the background.",
                    "task_id": task.id,
                    "max_pages": max_pages,
                    "estimated_books": max_pages * 20,
                },
                status=status.HTTP_202_ACCEPTED,
            )
        except Exception as exc:
            logger.error(f"Failed to queue scrape task: {exc}")
            return Response(
                {
                    "error": str(exc),
                    "message": "Make sure the Celery worker is running.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


# ---------------------------------------------------------------
# POST /api/qa/
# ---------------------------------------------------------------
class RAGQueryView(APIView):
    """
    RAG-based Q&A endpoint.

    Body: { question: str, top_k: int (optional, 1–10) }
    Returns: { question, answer, sources }
    """

    def post(self, request):
        serializer = RAGQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        question = serializer.validated_data["question"]
        top_k = serializer.validated_data.get("top_k", 5)

        logger.info(f"RAG query: '{question[:80]}'")

        try:
            from .rag import rag_query
            result = rag_query(question, top_k=top_k)

            # Persist to chat history
            ChatHistory.objects.create(
                question=question,
                answer=result["answer"],
                sources=result["sources"],
            )
            # Invalidate chat history cache
            cache.delete("chat_history:all")

            return Response(
                {
                    "question": question,
                    "answer": result["answer"],
                    "sources": result["sources"],
                }
            )
        except Exception as exc:
            logger.error(f"RAG query failed: {exc}")
            return Response(
                {"error": "Failed to process question.", "detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ---------------------------------------------------------------
# GET /api/chat/history/
# ---------------------------------------------------------------
class ChatHistoryView(generics.ListAPIView):
    """Return the full saved chat history, newest first."""

    serializer_class = ChatHistorySerializer
    pagination_class = BookPagination

    def get_queryset(self):
        return ChatHistory.objects.all()

    def list(self, request, *args, **kwargs):
        cache_key = "chat_history:all"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=60)
        return response


# ---------------------------------------------------------------
# GET /api/genres/
# ---------------------------------------------------------------
@api_view(["GET"])
def genres_list(request):
    """Return all distinct genres present in the database."""
    cache_key = "genres_list"
    cached = cache.get(cache_key)
    if cached:
        return Response(cached)

    genres = (
        Book.objects.exclude(genre="")
        .values_list("genre", flat=True)
        .distinct()
        .order_by("genre")
    )
    result = list(genres)
    cache.set(cache_key, result, timeout=600)
    return Response(result)


# ---------------------------------------------------------------
# GET /api/stats/
# ---------------------------------------------------------------
@api_view(["GET"])
def stats_view(request):
    """Return summary statistics about the book database."""
    cache_key = "db_stats"
    cached = cache.get(cache_key)
    if cached:
        return Response(cached)

    stats = {
        "total_books": Book.objects.count(),
        "processed_books": Book.objects.filter(processed=True).count(),
        "pending_books": Book.objects.filter(processed=False).count(),
        "total_genres": Book.objects.exclude(genre="").values("genre").distinct().count(),
        "total_chats": ChatHistory.objects.count(),
    }
    cache.set(cache_key, stats, timeout=120)
    return Response(stats)
