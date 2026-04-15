"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const NAV_LINKS = [
  { href: "/", label: "📚 Library", id: "nav-library" },
  { href: "/qa", label: "💬 Ask AI", id: "nav-qa" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav
      style={{
        position: "sticky",
        top: 0,
        zIndex: 50,
        borderBottom: "1px solid var(--color-border)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        background: "rgba(8, 11, 20, 0.85)",
      }}
    >
      <div
        style={{
          maxWidth: "1280px",
          margin: "0 auto",
          padding: "0 24px",
          height: "64px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        {/* Logo */}
        <Link
          href="/"
          style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: "10px" }}
        >
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: "10px",
              background: "var(--gradient-primary)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "18px",
            }}
          >
            📖
          </div>
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontWeight: 800,
              fontSize: "18px",
              background: "var(--gradient-primary)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            BookAutomation
          </span>
        </Link>

        {/* Desktop Nav */}
        <div style={{ display: "flex", gap: "4px", alignItems: "center" }}>
          {NAV_LINKS.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                id={link.id}
                style={{
                  padding: "8px 16px",
                  borderRadius: "8px",
                  fontWeight: 500,
                  fontSize: "14px",
                  textDecoration: "none",
                  transition: "all 0.2s ease",
                  color: isActive ? "white" : "var(--color-text-secondary)",
                  background: isActive ? "rgba(99, 102, 241, 0.2)" : "transparent",
                  border: isActive
                    ? "1px solid rgba(99, 102, 241, 0.4)"
                    : "1px solid transparent",
                }}
              >
                {link.label}
              </Link>
            );
          })}
        </div>

        {/* GitHub badge */}
        <a
          href="https://bookautomation.onrender.com"
          target="_blank"
          rel="noopener noreferrer"
          title="API Docs"
          style={{
            padding: "8px 14px",
            borderRadius: "8px",
            fontSize: "12px",
            fontWeight: 500,
            color: "var(--color-text-muted)",
            border: "1px solid var(--color-border)",
            textDecoration: "none",
            transition: "all 0.2s ease",
          }}
        >
          API ↗
        </a>
      </div>
    </nav>
  );
}
