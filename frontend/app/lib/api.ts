/**
 * Centralized API Client
 * =======================
 * All backend calls go through this module.
 * Base URL is set via NEXT_PUBLIC_API_URL env variable.
 */

import type {
  Book,
  ChatMessage,
  PaginatedResponse,
  RAGResponse,
  RecommendationsResponse,
  ScrapeResponse,
  Stats,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

// ── Generic fetch wrapper ────────────────────────────────────────
async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const message =
      err.error || err.detail || err.message || `HTTP ${res.status}`;
    throw new Error(message);
  }

  return res.json() as Promise<T>;
}

// ── Books ────────────────────────────────────────────────────────
export const getBooks = (params?: Record<string, string>) => {
  const qs = params ? `?${new URLSearchParams(params)}` : "";
  return request<PaginatedResponse<Book>>(`/books/${qs}`);
};

export const getBook = (id: string) =>
  request<Book>(`/books/${id}/`);

export const getRecommendations = (id: string) =>
  request<RecommendationsResponse>(`/books/${id}/recommendations/`);

export const uploadBook = (data: Partial<Book>) =>
  request<{ book: Book; book_id: string; task_queued: boolean }>("/books/upload/", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const triggerScrape = (maxPages: number) =>
  request<ScrapeResponse>("/books/scrape/", {
    method: "POST",
    body: JSON.stringify({ max_pages: maxPages }),
  });

// ── Q&A ─────────────────────────────────────────────────────────
export const askQuestion = (question: string, topK = 5) =>
  request<RAGResponse>("/qa/", {
    method: "POST",
    body: JSON.stringify({ question, top_k: topK }),
  });

// ── Chat History ─────────────────────────────────────────────────
export const getChatHistory = () =>
  request<PaginatedResponse<ChatMessage>>("/chat/history/");

// ── Utility ──────────────────────────────────────────────────────
export const getGenres = () => request<string[]>("/genres/");
export const getStats = () => request<Stats>("/stats/");
