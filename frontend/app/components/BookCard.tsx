"use client";

import Link from "next/link";
import type { Book } from "../lib/types";
import GenreBadge from "./GenreBadge";
import RatingStars from "./RatingStars";

interface BookCardProps {
  book: Book;
}

const SENTIMENT_COLORS: Record<string, string> = {
  Uplifting: "#10b981",
  Dark: "#64748b",
  Suspenseful: "#f59e0b",
  Romantic: "#ec4899",
  Humorous: "#f97316",
  Inspirational: "#6366f1",
  Melancholic: "#8b5cf6",
  Adventurous: "#06b6d4",
  "Thought-provoking": "#a78bfa",
  Neutral: "#64748b",
};

function CoverImage({ src, alt, processed }: { src: string; alt: string; processed: boolean }) {
  return (
    <div
      style={{
        width: "100%",
        aspectRatio: "2/3",
        borderRadius: "10px 10px 0 0",
        overflow: "hidden",
        background: "linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%)",
        position: "relative",
      }}
    >
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={src}
          alt={alt}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = "none";
          }}
        />
      ) : (
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: "8px",
          }}
        >
          <span style={{ fontSize: "40px" }}>📚</span>
          <span style={{ fontSize: "11px", color: "var(--color-text-muted)", textAlign: "center", padding: "0 12px" }}>
            {alt}
          </span>
        </div>
      )}
 
      {/* Processed badge */}
      {processed && (
        <div
          style={{
            position: "absolute",
            top: "8px",
            right: "8px",
            padding: "3px 8px",
            borderRadius: "20px",
            fontSize: "10px",
            fontWeight: 600,
            background: "rgba(16, 185, 129, 0.15)",
            border: "1px solid rgba(16, 185, 129, 0.4)",
            color: "#10b981",
          }}
        >
          AI Ready
        </div>
      )}
    </div>
  );
}

export default function BookCard({ book }: BookCardProps) {
  const sentimentColor = SENTIMENT_COLORS[book.sentiment] || "#64748b";

  return (
    <Link
      href={`/books/${book.id}`}
      style={{ textDecoration: "none" }}
      id={`book-card-${book.id}`}
    >
      <div
        className="glass-card fade-in"
        style={{
          height: "100%",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          cursor: "pointer",
        }}
      >
        {/* Cover */}
        <CoverImage src={book.cover_image} alt={book.title} processed={book.processed} />

        {/* Content */}
        <div style={{ padding: "14px", display: "flex", flexDirection: "column", gap: "8px", flex: 1 }}>
          {/* Genre */}
          {book.genre && <GenreBadge genre={book.genre} />}

          {/* Title */}
          <h3
            style={{
              fontSize: "14px",
              fontWeight: 700,
              lineHeight: 1.3,
              color: "var(--color-text-primary)",
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
            }}
          >
            {book.title}
          </h3>

          {/* Author */}
          <p style={{ fontSize: "12px", color: "var(--color-text-muted)", fontWeight: 500 }}>
            {book.author || "Unknown Author"}
          </p>

          {/* Rating */}
          {book.rating !== null && book.rating !== undefined && (
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <RatingStars rating={book.rating} size={12} />
              <span style={{ fontSize: "12px", color: "var(--color-text-secondary)" }}>
                {book.rating.toFixed(1)}
              </span>
            </div>
          )}

          {/* Spacer */}
          <div style={{ flex: 1 }} />

          {/* Footer: price + sentiment */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              paddingTop: "8px",
              borderTop: "1px solid var(--color-border)",
            }}
          >
            <span style={{ fontSize: "13px", fontWeight: 700, color: "var(--color-primary-light)" }}>
              {book.price || "—"}
            </span>

            {book.sentiment && (
              <span
                className="badge"
                style={{
                  background: `${sentimentColor}18`,
                  border: `1px solid ${sentimentColor}40`,
                  color: sentimentColor,
                  fontSize: "10px",
                }}
              >
                {book.sentiment}
              </span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}
