"""
DRF Serializers for BookAutomation
====================================
Handles serialization/deserialization for all API endpoints.
"""

from rest_framework import serializers

from .models import Book, BookChunk, ChatHistory


class BookChunkSerializer(serializers.ModelSerializer):
    """Lightweight serializer for text chunks (used in BookDetailSerializer)."""

    class Meta:
        model = BookChunk
        fields = ["id", "chunk_index", "chunk_text", "embedding_id"]


class BookListSerializer(serializers.ModelSerializer):
    """
    Compact serializer for the book listing / dashboard view.
    Excludes heavy fields like 'chunks' for performance.
    """

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "rating",
            "num_reviews",
            "description",
            "book_url",
            "cover_image",
            "genre",
            "sentiment",
            "summary",
            "price",
            "availability",
            "processed",
            "created_at",
        ]


class BookDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for the book detail page.
    Includes nested chunks and all AI insight fields.
    """

    chunks = BookChunkSerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "rating",
            "num_reviews",
            "description",
            "book_url",
            "cover_image",
            "genre",
            "sentiment",
            "summary",
            "recommendations",
            "price",
            "availability",
            "processed",
            "created_at",
            "updated_at",
            "chunks",
        ]


class BookUploadSerializer(serializers.ModelSerializer):
    """Serializer for the manual book upload endpoint (POST /api/books/upload/)."""

    class Meta:
        model = Book
        fields = [
            "title",
            "author",
            "rating",
            "num_reviews",
            "description",
            "book_url",
            "cover_image",
            "genre",
        ]

    def validate_book_url(self, value):
        """Ensure no duplicate book URLs in the database."""
        if Book.objects.filter(book_url=value).exists():
            raise serializers.ValidationError(
                "A book with this URL already exists in the database."
            )
        return value


class ChatHistorySerializer(serializers.ModelSerializer):
    """Serializer for chat history entries."""

    class Meta:
        model = ChatHistory
        fields = ["id", "question", "answer", "sources", "created_at"]
        read_only_fields = ["id", "created_at"]


class RAGQuerySerializer(serializers.Serializer):
    """Input validation for the POST /api/qa/ endpoint."""

    question = serializers.CharField(
        min_length=3,
        max_length=1000,
        help_text="Your question about books in the database.",
    )
    top_k = serializers.IntegerField(
        default=5,
        min_value=1,
        max_value=10,
        required=False,
        help_text="Number of text chunks to retrieve as context (1–10).",
    )


class ScrapeRequestSerializer(serializers.Serializer):
    """Input validation for the POST /api/books/scrape/ endpoint."""

    max_pages = serializers.IntegerField(
        default=5,
        min_value=1,
        max_value=50,
        required=False,
        help_text=(
            "Number of catalogue pages to scrape (1–50). "
            "Each page has ~20 books, so 50 pages = ~1000 books."
        ),
    )
