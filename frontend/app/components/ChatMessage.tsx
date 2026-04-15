// Chat message bubble component for the Q&A interface

import type { Source } from "../lib/types";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  timestamp?: string;
}

export default function ChatMessage({ role, content, sources, timestamp }: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <div
      className="fade-in"
      style={{
        display: "flex",
        flexDirection: isUser ? "row-reverse" : "row",
        gap: "12px",
        alignItems: "flex-start",
        marginBottom: "20px",
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: "50%",
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "16px",
          background: isUser
            ? "rgba(99, 102, 241, 0.2)"
            : "rgba(139, 92, 246, 0.2)",
          border: `1px solid ${isUser ? "rgba(99,102,241,0.4)" : "rgba(139,92,246,0.4)"}`,
        }}
      >
        {isUser ? "👤" : "🤖"}
      </div>

      {/* Bubble */}
      <div
        style={{
          maxWidth: "75%",
          display: "flex",
          flexDirection: "column",
          gap: "8px",
          alignItems: isUser ? "flex-end" : "flex-start",
        }}
      >
        <div
          style={{
            padding: "14px 18px",
            borderRadius: isUser ? "18px 6px 18px 18px" : "6px 18px 18px 18px",
            background: isUser
              ? "linear-gradient(135deg, #6366f1, #8b5cf6)"
              : "rgba(255,255,255,0.05)",
            border: isUser ? "none" : "1px solid var(--color-border)",
            color: "var(--color-text-primary)",
            fontSize: "14px",
            lineHeight: 1.7,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {content}
        </div>

        {/* Source Citations */}
        {!isUser && sources && sources.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "6px", width: "100%" }}>
            <p
              style={{
                fontSize: "11px",
                color: "var(--color-text-muted)",
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              Sources
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
              {sources.map((src, i) => (
                <div key={i} className="source-card" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <span style={{ fontSize: "11px", color: "var(--color-accent)" }}>📖</span>
                  <span style={{ color: "var(--color-text-secondary)" }}>{src.book_title}</span>
                  <span
                    style={{
                      background: "rgba(99,102,241,0.15)",
                      color: "var(--color-primary-light)",
                      padding: "1px 6px",
                      borderRadius: "10px",
                      fontSize: "10px",
                      fontWeight: 600,
                    }}
                  >
                    {Math.round(src.relevance_score * 100)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Timestamp */}
        {timestamp && (
          <span style={{ fontSize: "10px", color: "var(--color-text-muted)" }}>
            {new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>
        )}
      </div>
    </div>
  );
}

// Typing indicator shown while waiting for AI response
export function TypingIndicator() {
  return (
    <div style={{ display: "flex", gap: "12px", alignItems: "flex-start", marginBottom: "20px" }}>
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: "50%",
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "16px",
          background: "rgba(139, 92, 246, 0.2)",
          border: "1px solid rgba(139,92,246,0.4)",
        }}
      >
        🤖
      </div>
      <div
        style={{
          padding: "16px 20px",
          borderRadius: "6px 18px 18px 18px",
          background: "rgba(255,255,255,0.05)",
          border: "1px solid var(--color-border)",
          display: "flex",
          gap: "6px",
          alignItems: "center",
        }}
      >
        <div className="typing-dot" />
        <div className="typing-dot" />
        <div className="typing-dot" />
      </div>
    </div>
  );
}
