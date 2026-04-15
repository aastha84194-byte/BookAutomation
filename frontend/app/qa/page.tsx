"use client";

import { useEffect, useRef, useState } from "react";
import type { ChatMessage as ChatMsg, RAGResponse, Source } from "../lib/types";
import { askQuestion, getChatHistory } from "../lib/api";
import ChatMessage, { TypingIndicator } from "../components/ChatMessage";

// Sample questions to help users get started
const SAMPLE_QUESTIONS = [
  "What are the best mystery books in your collection?",
  "Recommend a book similar to a dark thriller",
  "Which books have the highest ratings?",
  "Tell me about books in the Fantasy genre",
  "What are some uplifting books to read?",
];

interface LocalMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  timestamp: string;
}

export default function QAPage() {
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Load chat history on mount
  useEffect(() => {
    getChatHistory()
      .then((data) => {
        // Convert history to local messages (reversed — API returns newest first)
        const historical: LocalMessage[] = [];
        const reversed = [...data.results].reverse();
        for (const item of reversed) {
          historical.push({
            id: `${item.id}-q`,
            role: "user",
            content: item.question,
            timestamp: item.created_at,
          });
          historical.push({
            id: `${item.id}-a`,
            role: "assistant",
            content: item.answer,
            sources: item.sources,
            timestamp: item.created_at,
          });
        }
        setMessages(historical);
      })
      .catch(console.error)
      .finally(() => setHistoryLoading(false));
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async (question: string) => {
    if (!question.trim() || loading) return;

    const userMsg: LocalMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: question.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const res: RAGResponse = await askQuestion(question.trim());
      const aiMsg: LocalMessage = {
        id: `ai-${Date.now()}`,
        role: "assistant",
        content: res.answer,
        sources: res.sources,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      setError((err as Error).message || "Failed to get answer");
      const errMsg: LocalMessage = {
        id: `err-${Date.now()}`,
        role: "assistant",
        content: `⚠️ Error: ${(err as Error).message}. Make sure the backend is running.`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const clearHistory = () => setMessages([]);

  return (
    <div
      style={{
        maxWidth: "900px",
        margin: "0 auto",
        padding: "24px",
        height: "calc(100vh - 130px)",
        display: "flex",
        flexDirection: "column",
        gap: "20px",
      }}
    >
      {/* ── Header ──────────────────────────────────────────────── */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1
            style={{
              fontSize: "28px",
              fontWeight: 800,
              background: "linear-gradient(135deg, #f0f0ff, #a78bfa)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
              marginBottom: "4px",
            }}
          >
            💬 Ask About Books
          </h1>
          <p style={{ fontSize: "14px", color: "var(--color-text-muted)" }}>
            Powered by Gemini AI &amp; RAG pipeline · Ask anything about the book library
          </p>
        </div>
        {messages.length > 0 && (
          <button onClick={clearHistory} className="btn-secondary" style={{ fontSize: "12px" }}>
            🗑 Clear Chat
          </button>
        )}
      </div>

      {/* ── Chat Container ───────────────────────────────────────── */}
      <div
        className="glass-card"
        style={{
          flex: 1,
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* Messages area */}
        <div
          id="messages-area"
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "24px",
          }}
        >
          {/* Welcome state */}
          {!historyLoading && messages.length === 0 && (
            <div style={{ textAlign: "center", padding: "40px 20px" }}>
              <div style={{ fontSize: "56px", marginBottom: "16px" }}>🤖</div>
              <h2 style={{ marginBottom: "8px", fontSize: "20px" }}>Ask Me About Books</h2>
              <p style={{ color: "var(--color-text-muted)", marginBottom: "28px", fontSize: "14px" }}>
                I&apos;ll search through the book database and give you answers with citations.
              </p>

              {/* Sample questions grid */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
                  gap: "10px",
                  maxWidth: "680px",
                  margin: "0 auto",
                }}
              >
                {SAMPLE_QUESTIONS.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(q)}
                    style={{
                      padding: "10px 14px",
                      borderRadius: "10px",
                      background: "rgba(99,102,241,0.06)",
                      border: "1px solid var(--color-border)",
                      color: "var(--color-text-secondary)",
                      fontSize: "13px",
                      cursor: "pointer",
                      textAlign: "left",
                      lineHeight: 1.4,
                      transition: "all 0.2s ease",
                    }}
                    onMouseEnter={(e) => {
                      (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--color-primary)";
                      (e.currentTarget as HTMLButtonElement).style.color = "var(--color-text-primary)";
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--color-border)";
                      (e.currentTarget as HTMLButtonElement).style.color = "var(--color-text-secondary)";
                    }}
                  >
                    &ldquo;{q}&rdquo;
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Chat messages */}
          {messages.map((msg) => (
            <ChatMessage
              key={msg.id}
              role={msg.role}
              content={msg.content}
              sources={msg.sources}
              timestamp={msg.timestamp}
            />
          ))}

          {/* Typing indicator */}
          {loading && <TypingIndicator />}

          <div ref={messagesEndRef} />
        </div>

        {/* ── Input area ──────────────────────────────────────── */}
        <div
          style={{
            padding: "16px 20px",
            borderTop: "1px solid var(--color-border)",
            background: "rgba(0,0,0,0.2)",
          }}
        >
          <div style={{ display: "flex", gap: "12px", alignItems: "flex-end" }}>
            <textarea
              ref={inputRef}
              id="question-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about books… (Enter to send, Shift+Enter for newline)"
              disabled={loading}
              rows={2}
              style={{
                flex: 1,
                padding: "12px 16px",
                background: "rgba(255,255,255,0.04)",
                border: "1px solid var(--color-border)",
                borderRadius: "12px",
                color: "var(--color-text-primary)",
                fontSize: "14px",
                resize: "none",
                outline: "none",
                fontFamily: "var(--font-sans)",
                lineHeight: 1.5,
                transition: "border-color 0.2s ease",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "var(--color-primary)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "var(--color-border)";
              }}
            />
            <button
              id="send-button"
              onClick={() => sendMessage(input)}
              disabled={loading || !input.trim()}
              className="btn-primary"
              style={{
                height: "52px",
                padding: "0 20px",
                opacity: loading || !input.trim() ? 0.5 : 1,
                flexShrink: 0,
              }}
            >
              {loading ? "⏳" : "➤ Send"}
            </button>
          </div>
          <p style={{ fontSize: "11px", color: "var(--color-text-muted)", marginTop: "8px" }}>
            💡 Tip: Ask about genres, recommendations, ratings, or specific book topics.
          </p>
        </div>
      </div>
    </div>
  );
}
