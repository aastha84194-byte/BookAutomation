"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import type { Book, RecommendationsResponse } from "../../lib/types";
import { getBook, getRecommendations } from "../../lib/api";
import BookCard from "../../components/BookCard";
import { BookDetailSkeleton } from "../../components/LoadingSkeleton";
import GenreBadge from "../../components/GenreBadge";
import RatingStars from "../../components/RatingStars";

const SENTIMENT_ICONS: Record<string, string> = {
  Uplifting: "🌟", Dark: "🌑", Neutral: "⚖️", Suspenseful: "😰",
  Romantic: "💕", Humorous: "😄", Inspirational: "💫", Melancholic: "🌧️",
  Adventurous: "🗺️", "Thought-provoking": "🤔",
};

function InsightCard({
  icon, title, content, color = "#6366f1",
}: { icon: string; title: string; content: string; color?: string }) {
  return (
    <div
      className="glass-card"
      style={{ padding: "20px", borderLeft: `3px solid ${color}` }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          marginBottom: "10px",
        }}
      >
        <span style={{ fontSize: "18px" }}>{icon}</span>
        <h3 style={{ fontSize: "13px", fontWeight: 700, color, textTransform: "uppercase", letterSpacing: "0.05em" }}>
          {title}
        </h3>
      </div>
      <p style={{ fontSize: "14px", color: "var(--color-text-secondary)", lineHeight: 1.7 }}>
        {content}
      </p>
    </div>
  );
}

export default function BookDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [book, setBook] = useState<Book | null>(null);
  const [recommendations, setRecommendations] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [descExpanded, setDescExpanded] = useState(false);

  useEffect(() => {
    if (!id) return;

    Promise.all([getBook(id), getRecommendations(id)])
      .then(([bookData, recData]: [Book, RecommendationsResponse]) => {
        setBook(bookData);
        setRecommendations(recData.recommendations || []);
      })
      .catch((err) => setError((err as Error).message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "32px 24px" }}>
        <BookDetailSkeleton />
      </div>
    );
  }

  if (error || !book) {
    return (
      <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "32px 24px", textAlign: "center" }}>
        <p style={{ fontSize: "48px", marginBottom: "16px" }}>⚠️</p>
        <h2 style={{ marginBottom: "8px" }}>Book Not Found</h2>
        <p style={{ color: "var(--color-text-muted)", marginBottom: "24px" }}>{error}</p>
        <Link href="/" className="btn-primary">← Back to Library</Link>
      </div>
    );
  }

  const truncatedDesc = book.description.length > 300
    ? book.description.slice(0, 300) + "…"
    : book.description;

  return (
    <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "32px 24px" }}>
      {/* ── Breadcrumb ──────────────────────────────────────────── */}
      <div style={{ marginBottom: "28px", display: "flex", alignItems: "center", gap: "8px" }}>
        <Link
          href="/"
          style={{ color: "var(--color-text-muted)", textDecoration: "none", fontSize: "14px" }}
        >
          📚 Library
        </Link>
        <span style={{ color: "var(--color-text-muted)" }}>›</span>
        <span style={{ fontSize: "14px", color: "var(--color-text-secondary)" }}>
          {book.title.length > 40 ? book.title.slice(0, 40) + "…" : book.title}
        </span>
      </div>

      {/* ── Main Layout (cover + details) ───────────────────────── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "280px 1fr",
          gap: "40px",
          marginBottom: "48px",
        }}
      >
        {/* ── Left: Cover ─────────────────────────────────────── */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div
            style={{
              borderRadius: "16px",
              overflow: "hidden",
              border: "1px solid var(--color-border)",
              aspectRatio: "2/3",
              background: "linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {book.cover_image ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={book.cover_image}
                alt={book.title}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = "none";
                }}
              />
            ) : (
              <span style={{ fontSize: "64px" }}>📚</span>
            )}
          </div>

          {/* Metadata table */}
          <div className="glass-card" style={{ padding: "16px" }}>
            {[
              { label: "Price", value: book.price || "—" },
              { label: "Availability", value: book.availability || "—" },
              { label: "Reviews", value: book.num_reviews?.toString() || "0" },
            ].map(({ label, value }) => (
              <div
                key={label}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "8px 0",
                  borderBottom: "1px solid var(--color-border)",
                  fontSize: "13px",
                }}
              >
                <span style={{ color: "var(--color-text-muted)" }}>{label}</span>
                <span style={{ color: "var(--color-text-primary)", fontWeight: 500 }}>{value}</span>
              </div>
            ))}
            {book.processed && (
              <div style={{ marginTop: "12px" }}>
                <span
                  className="badge"
                  style={{
                    background: "rgba(16,185,129,0.12)",
                    border: "1px solid rgba(16,185,129,0.3)",
                    color: "#10b981",
                    width: "100%",
                    justifyContent: "center",
                    padding: "6px",
                  }}
                >
                  ✓ AI Insights Ready
                </span>
              </div>
            )}
          </div>

          {/* Link to original */}
          <a
            href={book.book_url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary"
            style={{ justifyContent: "center", textAlign: "center" }}
          >
            View Source ↗
          </a>
        </div>

        {/* ── Right: Details ───────────────────────────────────── */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* Badges row */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {book.genre && <GenreBadge genre={book.genre} size="md" />}
            {book.sentiment && (
              <span
                className="badge"
                style={{
                  background: "rgba(139,92,246,0.12)",
                  border: "1px solid rgba(139,92,246,0.3)",
                  color: "#a78bfa",
                  fontSize: "12px",
                  padding: "5px 12px",
                }}
              >
                {SENTIMENT_ICONS[book.sentiment] || "🎭"} {book.sentiment}
              </span>
            )}
          </div>

          {/* Title */}
          <h1 style={{ fontSize: "clamp(22px, 3vw, 36px)", lineHeight: 1.15 }}>
            {book.title}
          </h1>

          {/* Author */}
          <p style={{ fontSize: "16px", color: "var(--color-text-secondary)" }}>
            by <strong style={{ color: "var(--color-text-primary)" }}>{book.author || "Unknown"}</strong>
          </p>

          {/* Rating */}
          {book.rating !== null && book.rating !== undefined && (
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <RatingStars rating={book.rating} size={18} />
              <span style={{ fontSize: "20px", fontWeight: 700, color: "var(--color-primary-light)" }}>
                {book.rating.toFixed(1)}
              </span>
              <span style={{ fontSize: "14px", color: "var(--color-text-muted)" }}>/ 5.0</span>
            </div>
          )}

          {/* Description */}
          {book.description && (
            <div className="glass-card" style={{ padding: "18px" }}>
              <h3 style={{ fontSize: "13px", color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "10px" }}>
                Description
              </h3>
              <p style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                {descExpanded ? book.description : truncatedDesc}
              </p>
              {book.description.length > 300 && (
                <button
                  onClick={() => setDescExpanded(!descExpanded)}
                  style={{
                    marginTop: "8px",
                    background: "none",
                    border: "none",
                    color: "var(--color-primary-light)",
                    cursor: "pointer",
                    fontSize: "13px",
                    fontWeight: 600,
                    padding: 0,
                  }}
                >
                  {descExpanded ? "Show less ↑" : "Read more ↓"}
                </button>
              )}
            </div>
          )}

          {/* AI Insights */}
          {book.processed && (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <h2 style={{ fontSize: "16px", color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                🤖 AI Insights
              </h2>
              {book.summary && (
                <InsightCard
                  icon="📝"
                  title="AI Summary"
                  content={book.summary}
                  color="#6366f1"
                />
              )}
              {book.genre && (
                <InsightCard
                  icon="🏷️"
                  title="Genre Classification"
                  content={`This book is classified as ${book.genre} based on its content, themes, and writing style.`}
                  color="#8b5cf6"
                />
              )}
              {book.sentiment && (
                <InsightCard
                  icon={SENTIMENT_ICONS[book.sentiment] || "🎭"}
                  title="Sentiment Analysis"
                  content={`The tone of this book is predominantly ${book.sentiment.toLowerCase()}.`}
                  color="#a78bfa"
                />
              )}
            </div>
          )}

          {/* Ask AI button */}
          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
            <Link
              href={`/qa?book=${encodeURIComponent(book.title)}`}
              className="btn-primary"
            >
              💬 Ask AI About This Book
            </Link>
            <Link href="/" className="btn-secondary">
              ← Back to Library
            </Link>
          </div>
        </div>
      </div>

      {/* ── Recommendations ─────────────────────────────────────── */}
      {recommendations.length > 0 && (
        <section>
          <h2
            style={{
              fontSize: "22px",
              fontWeight: 700,
              marginBottom: "20px",
              display: "flex",
              alignItems: "center",
              gap: "10px",
            }}
          >
            <span className="gradient-text">✨ You Might Also Like</span>
          </h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
              gap: "16px",
            }}
          >
            {recommendations.slice(0, 6).map((rec) => (
              <BookCard key={rec.id} book={rec} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
