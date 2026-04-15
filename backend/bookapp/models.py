"""
Database Models for BookAutomation
====================================
Tables:
  - Book          : Scraped book metadata + AI insights
  - BookChunk     : Text chunks for RAG (linked to Book)
  - ChatHistory   : Saved Q&A interactions
  - AICache       : Cached AI responses (soft-TTL)
"""

import uuid

from django.db import models
from django.utils import timezone
from pgvector.django import VectorField


class Book(models.Model):
    """
    Stores book metadata scraped from books.toscrape.com,
    plus AI-generated insights (summary, genre, sentiment, recommendations).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # --- Scraped Metadata ---
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=300, default="Unknown", blank=True)
    rating = models.FloatField(null=True, blank=True, help_text="Rating out of 5.0")
    num_reviews = models.IntegerField(default=0, blank=True)
    description = models.TextField(blank=True)
    book_url = models.URLField(max_length=1000, unique=True)
    cover_image = models.URLField(max_length=1000, blank=True)
    price = models.CharField(max_length=50, blank=True)
    availability = models.CharField(max_length=100, blank=True)

    # --- AI-Generated Insights ---
    genre = models.CharField(max_length=200, blank=True)
    sentiment = models.CharField(
        max_length=100,
        blank=True,
        help_text="Tone: Uplifting, Dark, Neutral, etc.",
    )
    summary = models.TextField(blank=True, help_text="AI-generated book summary")
    recommendations = models.JSONField(
        default=list,
        blank=True,
        help_text="List of recommended book titles",
    )

    # --- Processing Status ---
    processed = models.BooleanField(
        default=False,
        help_text="True once AI insights and embeddings are generated",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "books"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.author})"


class BookChunk(models.Model):
    """
    Stores text chunks of a book for the RAG pipeline.
    Each chunk is embedded and indexed in ChromaDB.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="chunks")
    chunk_text = models.TextField()
    chunk_index = models.IntegerField(help_text="Position in the sequence of chunks")
    embedding = VectorField(
        dimensions=3072,
        null=True,
        blank=True,
        help_text="3072-dim vector from Gemini",
    )
    embedding_id = models.CharField(
        max_length=200,
        blank=True,
        help_text="ChromaDB document ID for this chunk",
    )

    class Meta:
        db_table = "book_chunks"
        ordering = ["chunk_index"]
        unique_together = [["book", "chunk_index"]]

    def __str__(self):
        return f"{self.book.title} — Chunk #{self.chunk_index}"


class ChatHistory(models.Model):
    """
    Persists all user Q&A interactions from the RAG pipeline.
    Sources field stores which book chunks contributed to the answer.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.TextField()
    answer = models.TextField()
    sources = models.JSONField(
        default=list,
        help_text="List of {book_id, book_title, chunk_index, relevance_score}",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_history"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Q: {self.question[:60]}..."


class AICache(models.Model):
    """
    Soft-TTL cache for AI-generated responses.
    Prevents redundant Gemini API calls for identical prompts.
    Cache key = MD5 hash of the prompt string.
    """

    cache_key = models.CharField(
        max_length=64,
        unique=True,
        help_text="MD5 hash of the prompt",
    )
    response = models.JSONField(help_text="Cached AI response payload")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(help_text="Soft expiry timestamp")

    class Meta:
        db_table = "ai_cache"

    def is_expired(self) -> bool:
        """Check if this cache entry has passed its soft TTL."""
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"AICache [{self.cache_key[:16]}...] expires {self.expires_at:%Y-%m-%d %H:%M}"
