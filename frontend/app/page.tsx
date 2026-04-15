"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Book, PaginatedResponse, Stats } from "./lib/types";
import { getBooks, getGenres, getStats, triggerScrape } from "./lib/api";
import BookCard from "./components/BookCard";
import { BookGridSkeleton, StatCardSkeleton } from "./components/LoadingSkeleton";

// ── Stat Card ────────────────────────────────────────────────────
function StatCard({
  label,
  value,
  icon,
  color = "#6366f1",
}: {
  label: string;
  value: number | string;
  icon: string;
  color?: string;
}) {
  return (
    <div
      className="glass-card"
      style={{ padding: "20px 24px", display: "flex", alignItems: "center", gap: "16px" }}
    >
      <div
        style={{
          width: 48,
          height: 48,
          borderRadius: "12px",
          background: `${color}18`,
          border: `1px solid ${color}30`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "22px",
          flexShrink: 0,
        }}
      >
        {icon}
      </div>
      <div>
        <p
          style={{
            fontSize: "24px",
            fontWeight: 800,
            fontFamily: "var(--font-display)",
            color: "var(--color-text-primary)",
            lineHeight: 1,
          }}
        >
          {value}
        </p>
        <p style={{ fontSize: "13px", color: "var(--color-text-muted)", marginTop: "4px" }}>
          {label}
        </p>
      </div>
    </div>
  );
}

// ── Main Dashboard Page ──────────────────────────────────────────
export default function DashboardPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [genres, setGenres] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingStats, setLoadingStats] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [selectedGenre, setSelectedGenre] = useState("");
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // Scrape state
  const [scraping, setScraping] = useState(false);
  const [scrapeMsg, setScrapeMsg] = useState("");
  const [scrapePages, setScrapePages] = useState(5);

  const searchTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Fetch books with current filters
  const fetchBooks = useCallback(async (pageNum = 1, q = search, genre = selectedGenre) => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = { page: String(pageNum), page_size: "20" };
      if (q) params.search = q;
      if (genre) params.genre = genre;
      const data: PaginatedResponse<Book> = await getBooks(params);
      setBooks(data.results);
      setTotalCount(data.count);
    } catch (err) {
      setError((err as Error).message || "Failed to load books");
    } finally {
      setLoading(false);
    }
  }, [search, selectedGenre]);

  // Load initial data
  useEffect(() => {
    fetchBooks(1, "", "");
    getStats().then(setStats).catch(console.error).finally(() => setLoadingStats(false));
    getGenres().then(setGenres).catch(console.error);
  }, []);

  // Debounced search
  const handleSearchChange = (val: string) => {
    setSearch(val);
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => {
      setPage(1);
      fetchBooks(1, val, selectedGenre);
    }, 400);
  };

  const handleGenreChange = (genre: string) => {
    setSelectedGenre(genre);
    setPage(1);
    fetchBooks(1, search, genre);
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    fetchBooks(newPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleScrape = async () => {
    setScraping(true);
    setScrapeMsg("");
    try {
      const res = await triggerScrape(scrapePages);
      setScrapeMsg(`✅ ${res.message}`);
      setTimeout(() => {
        fetchBooks(1, search, selectedGenre);
        getStats().then(setStats);
      }, 2000);
    } catch (err) {
      setScrapeMsg(`❌ ${(err as Error).message}`);
    } finally {
      setScraping(false);
    }
  };

  const totalPages = Math.ceil(totalCount / 20);

  return (
    <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "32px 24px" }}>
      {/* ── Hero ────────────────────────────────────────────────── */}
      <div style={{ marginBottom: "40px", textAlign: "center" }}>
        <h1
          style={{
            fontSize: "clamp(28px, 4vw, 48px)",
            fontWeight: 800,
            marginBottom: "12px",
            background: "linear-gradient(135deg, #f0f0ff 0%, #818cf8 60%, #a78bfa 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}
        >
          📚 AI-Powered Book Library
        </h1>
        <p style={{ fontSize: "16px", color: "var(--color-text-secondary)", maxWidth: "600px", margin: "0 auto" }}>
          Browse books with AI-generated summaries, genre classification, sentiment analysis,
          and intelligent Q&amp;A
        </p>
      </div>

      {/* ── Stats ───────────────────────────────────────────────── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "16px",
          marginBottom: "32px",
        }}
      >
        {loadingStats ? (
          Array.from({ length: 4 }).map((_, i) => <StatCardSkeleton key={i} />)
        ) : stats ? (
          <>
            <StatCard label="Total Books" value={stats.total_books} icon="📚" color="#6366f1" />
            <StatCard label="AI Processed" value={stats.processed_books} icon="🤖" color="#10b981" />
            <StatCard label="Genres" value={stats.total_genres} icon="🏷️" color="#8b5cf6" />
            <StatCard label="Q&A Sessions" value={stats.total_chats} icon="💬" color="#f59e0b" />
          </>
        ) : null}
      </div>

      {/* ── Controls bar ────────────────────────────────────────── */}
      <div
        className="glass-card"
        style={{
          padding: "16px 20px",
          marginBottom: "28px",
          display: "flex",
          flexWrap: "wrap",
          gap: "12px",
          alignItems: "center",
        }}
      >
        {/* Search */}
        <div style={{ flex: "1 1 240px", position: "relative" }}>
          <span
            style={{
              position: "absolute",
              left: "14px",
              top: "50%",
              transform: "translateY(-50%)",
              color: "var(--color-text-muted)",
              fontSize: "16px",
            }}
          >
            🔍
          </span>
          <input
            id="search-input"
            type="text"
            placeholder="Search by title or author…"
            className="input-field"
            value={search}
            onChange={(e) => handleSearchChange(e.target.value)}
            style={{ paddingLeft: "40px" }}
          />
        </div>

        {/* Genre filter */}
        <select
          id="genre-filter"
          value={selectedGenre}
          onChange={(e) => handleGenreChange(e.target.value)}
          className="input-field"
          style={{ width: "auto", minWidth: "160px", cursor: "pointer" }}
        >
          <option value="">All Genres</option>
          {genres.map((g) => (
            <option key={g} value={g}>
              {g}
            </option>
          ))}
        </select>

        {/* Scrape controls */}
        <div style={{ display: "flex", gap: "8px", alignItems: "center", marginLeft: "auto" }}>
          <select
            value={scrapePages}
            onChange={(e) => setScrapePages(Number(e.target.value))}
            className="input-field"
            style={{ width: "auto", fontSize: "13px", cursor: "pointer" }}
          >
            {[1, 2, 5, 10, 20, 50].map((n) => (
              <option key={n} value={n}>
                {n} pages (~{n * 20} books)
              </option>
            ))}
          </select>
          <button
            id="scrape-button"
            onClick={handleScrape}
            disabled={scraping}
            className="btn-primary"
          >
            {scraping ? "⏳ Scraping…" : "🕷️ Scrape Books"}
          </button>
        </div>
      </div>

      {/* Scrape message */}
      {scrapeMsg && (
        <div
          className="fade-in"
          style={{
            marginBottom: "20px",
            padding: "12px 18px",
            borderRadius: "10px",
            background: scrapeMsg.includes("✅")
              ? "rgba(16,185,129,0.1)"
              : "rgba(239,68,68,0.1)",
            border: `1px solid ${scrapeMsg.includes("✅") ? "rgba(16,185,129,0.3)" : "rgba(239,68,68,0.3)"}`,
            fontSize: "14px",
            color: scrapeMsg.includes("✅") ? "#34d399" : "#f87171",
          }}
        >
          {scrapeMsg}
        </div>
      )}

      {/* ── Filter summary ──────────────────────────────────────── */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
        }}
      >
        <p style={{ fontSize: "14px", color: "var(--color-text-muted)" }}>
          {loading ? "Loading…" : `${totalCount.toLocaleString()} book${totalCount !== 1 ? "s" : ""} found`}
          {selectedGenre && ` in ${selectedGenre}`}
          {search && ` matching "${search}"`}
        </p>
        {(search || selectedGenre) && (
          <button
            onClick={() => {
              setSearch("");
              setSelectedGenre("");
              setPage(1);
              fetchBooks(1, "", "");
            }}
            className="btn-secondary"
            style={{ fontSize: "12px", padding: "6px 12px" }}
          >
            ✕ Clear filters
          </button>
        )}
      </div>

      {/* ── Book Grid ───────────────────────────────────────────── */}
      {error ? (
        <div
          className="glass-card"
          style={{
            padding: "40px",
            textAlign: "center",
            color: "var(--color-error)",
          }}
        >
          <p style={{ fontSize: "20px", marginBottom: "8px" }}>⚠️ {error}</p>
          <p style={{ fontSize: "14px", color: "var(--color-text-muted)" }}>
            Make sure the Django backend is running on port 8000.
          </p>
          <button
            onClick={() => fetchBooks(page)}
            className="btn-primary"
            style={{ marginTop: "16px" }}
          >
            Retry
          </button>
        </div>
      ) : loading ? (
        <BookGridSkeleton count={20} />
      ) : books.length === 0 ? (
        <div className="glass-card" style={{ padding: "60px", textAlign: "center" }}>
          <p style={{ fontSize: "48px", marginBottom: "16px" }}>📭</p>
          <h3 style={{ marginBottom: "8px" }}>No books found</h3>
          <p style={{ color: "var(--color-text-muted)", marginBottom: "24px" }}>
            {search || selectedGenre
              ? "Try adjusting your filters."
              : "Click 🕷️ Scrape Books to populate the library!"}
          </p>
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
            gap: "20px",
          }}
        >
          {books.map((book) => (
            <BookCard key={book.id} book={book} />
          ))}
        </div>
      )}

      {/* ── Pagination ──────────────────────────────────────────── */}
      {totalPages > 1 && (
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: "8px",
            marginTop: "40px",
            flexWrap: "wrap",
          }}
        >
          <button
            onClick={() => handlePageChange(page - 1)}
            disabled={page === 1}
            className="btn-secondary"
            style={{ opacity: page === 1 ? 0.4 : 1 }}
          >
            ← Prev
          </button>

          {Array.from({ length: Math.min(7, totalPages) }, (_, i) => {
            const p = page <= 4 ? i + 1 : page - 3 + i;
            if (p < 1 || p > totalPages) return null;
            return (
              <button
                key={p}
                onClick={() => handlePageChange(p)}
                className={page === p ? "btn-primary" : "btn-secondary"}
                style={{ minWidth: "40px" }}
              >
                {p}
              </button>
            );
          })}

          <button
            onClick={() => handlePageChange(page + 1)}
            disabled={page === totalPages}
            className="btn-secondary"
            style={{ opacity: page === totalPages ? 0.4 : 1 }}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
