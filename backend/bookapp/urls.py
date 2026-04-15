"""
URL Patterns for the bookapp API
===================================
All routes are mounted under /api/ by the root config/urls.py.
"""

from django.urls import path

from . import views

urlpatterns = [
    # ── Book endpoints ──────────────────────────────────────────
    path("books/", views.BookListView.as_view(), name="book-list"),

    # Fixed-string action paths must come before <uuid:id> patterns
    path("books/upload/", views.BookUploadView.as_view(), name="book-upload"),
    path("books/scrape/", views.ScrapeView.as_view(), name="book-scrape"),

    # UUID-based detail routes
    path("books/<uuid:id>/", views.BookDetailView.as_view(), name="book-detail"),
    path(
        "books/<uuid:id>/recommendations/",
        views.BookRecommendationsView.as_view(),
        name="book-recommendations",
    ),

    # ── Q&A / RAG ───────────────────────────────────────────────
    path("qa/", views.RAGQueryView.as_view(), name="rag-query"),

    # ── Chat History ────────────────────────────────────────────
    path("chat/history/", views.ChatHistoryView.as_view(), name="chat-history"),

    # ── Utility ─────────────────────────────────────────────────
    path("genres/", views.genres_list, name="genres-list"),
    path("stats/", views.stats_view, name="stats"),
]
