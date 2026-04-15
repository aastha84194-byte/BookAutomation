// ---------------------------------------------------------------
// TypeScript Types for the BookAutomation frontend
// ---------------------------------------------------------------

export interface Book {
  id: string;
  title: string;
  author: string;
  rating: number | null;
  num_reviews: number | null;
  description: string;
  book_url: string;
  cover_image: string;
  genre: string;
  sentiment: string;
  summary: string;
  recommendations: string[];
  price: string;
  availability: string;
  processed: boolean;
  created_at: string;
  updated_at?: string;
  chunks?: BookChunk[];
}

export interface BookChunk {
  id: string;
  chunk_index: number;
  chunk_text: string;
  embedding_id: string;
}

export interface Source {
  book_id: string;
  book_title: string;
  chunk_index: number;
  relevance_score: number;
}

export interface ChatMessage {
  id: string;
  question: string;
  answer: string;
  sources: Source[];
  created_at: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface RAGResponse {
  question: string;
  answer: string;
  sources: Source[];
}

export interface Stats {
  total_books: number;
  processed_books: number;
  pending_books: number;
  total_genres: number;
  total_chats: number;
}

export interface ScrapeResponse {
  message: string;
  task_id: string;
  max_pages: number;
  estimated_books: number;
}

export interface RecommendationsResponse {
  book_id: string;
  book_title: string;
  recommendations: Book[];
  ai_suggestions: string[];
}
