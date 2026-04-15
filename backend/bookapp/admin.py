"""
Django Admin Registration for BookAutomation Models.
"""

from django.contrib import admin

from .models import AICache, Book, BookChunk, ChatHistory


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Admin view for the Book model with filtering and search."""

    list_display = ["title", "author", "rating", "genre", "sentiment", "processed", "created_at"]
    list_filter = ["genre", "processed", "sentiment"]
    search_fields = ["title", "author", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
    list_per_page = 25


@admin.register(BookChunk)
class BookChunkAdmin(admin.ModelAdmin):
    """Admin view for text chunks used in the RAG pipeline."""

    list_display = ["book", "chunk_index", "embedding_id"]
    list_filter = ["book"]
    search_fields = ["chunk_text", "book__title"]
    readonly_fields = ["id"]
    list_per_page = 50


@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    """Admin view for saved Q&A chat interactions."""

    list_display = ["question_preview", "created_at"]
    readonly_fields = ["id", "created_at"]
    ordering = ["-created_at"]

    def question_preview(self, obj):
        """Truncated question for list display."""
        return obj.question[:80] + "..." if len(obj.question) > 80 else obj.question

    question_preview.short_description = "Question"


@admin.register(AICache)
class AICacheAdmin(admin.ModelAdmin):
    """Admin view for the AI response cache."""

    list_display = ["cache_key", "created_at", "expires_at"]
    readonly_fields = ["cache_key", "created_at"]
    ordering = ["-created_at"]
