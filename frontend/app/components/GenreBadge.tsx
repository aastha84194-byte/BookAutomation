// Genre badge with colour-coded labels by category

const GENRE_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  fiction: { bg: "rgba(99,102,241,0.12)", border: "rgba(99,102,241,0.3)", text: "#818cf8" },
  mystery: { bg: "rgba(245,158,11,0.12)", border: "rgba(245,158,11,0.3)", text: "#fbbf24" },
  romance: { bg: "rgba(236,72,153,0.12)", border: "rgba(236,72,153,0.3)", text: "#f472b6" },
  thriller: { bg: "rgba(239,68,68,0.12)", border: "rgba(239,68,68,0.3)", text: "#f87171" },
  fantasy: { bg: "rgba(139,92,246,0.12)", border: "rgba(139,92,246,0.3)", text: "#a78bfa" },
  "science fiction": { bg: "rgba(6,182,212,0.12)", border: "rgba(6,182,212,0.3)", text: "#22d3ee" },
  horror: { bg: "rgba(100,116,139,0.12)", border: "rgba(100,116,139,0.3)", text: "#94a3b8" },
  biography: { bg: "rgba(16,185,129,0.12)", border: "rgba(16,185,129,0.3)", text: "#34d399" },
  "self-help": { bg: "rgba(234,179,8,0.12)", border: "rgba(234,179,8,0.3)", text: "#facc15" },
  adventure: { bg: "rgba(249,115,22,0.12)", border: "rgba(249,115,22,0.3)", text: "#fb923c" },
  "historical fiction": { bg: "rgba(180,83,9,0.12)", border: "rgba(180,83,9,0.3)", text: "#f59e0b" },
  poetry: { bg: "rgba(167,139,250,0.12)", border: "rgba(167,139,250,0.3)", text: "#c4b5fd" },
  philosophy: { bg: "rgba(51,65,85,0.3)", border: "rgba(148,163,184,0.2)", text: "#94a3b8" },
  default: { bg: "rgba(99,102,241,0.08)", border: "rgba(99,102,241,0.2)", text: "#818cf8" },
};

function getColors(genre: string) {
  const key = genre.toLowerCase();
  for (const [pattern, colors] of Object.entries(GENRE_COLORS)) {
    if (pattern !== "default" && key.includes(pattern)) return colors;
  }
  return GENRE_COLORS.default;
}

interface GenreBadgeProps {
  genre: string;
  size?: "sm" | "md";
}

export default function GenreBadge({ genre, size = "sm" }: GenreBadgeProps) {
  if (!genre) return null;
  const colors = getColors(genre);
  const fontSize = size === "md" ? "12px" : "10px";
  const padding = size === "md" ? "5px 12px" : "3px 8px";

  return (
    <span
      className="badge"
      style={{
        background: colors.bg,
        border: `1px solid ${colors.border}`,
        color: colors.text,
        fontSize,
        padding,
      }}
    >
      {genre}
    </span>
  );
}
