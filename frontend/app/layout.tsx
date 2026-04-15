import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Navbar from "./components/Navbar";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "BookAutomation — AI-Powered Book Intelligence",
  description:
    "Discover, analyse, and ask questions about books using AI-powered RAG. Browse 1000+ books with AI summaries, genre classification, and semantic search.",
  keywords: ["books", "AI", "RAG", "book recommendations", "reading"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <Navbar />
        <main style={{ flex: 1 }}>{children}</main>

        {/* Footer */}
        <footer
          style={{
            borderTop: "1px solid var(--color-border)",
            padding: "20px 24px",
            textAlign: "center",
            color: "var(--color-text-muted)",
            fontSize: "13px",
          }}
        >
          BookAutomation &mdash; Powered by Gemini AI &amp; ChromaDB &bull; books.toscrape.com
        </footer>
      </body>
    </html>
  );
}
