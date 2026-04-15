// Star rating display component

interface RatingStarsProps {
  rating: number | null;
  size?: number;
  showNumber?: boolean;
}

export default function RatingStars({
  rating,
  size = 14,
  showNumber = false,
}: RatingStarsProps) {
  if (rating === null || rating === undefined) {
    return <span style={{ fontSize: size, color: "var(--color-text-muted)" }}>No rating</span>;
  }

  const full = Math.floor(rating);
  const half = rating - full >= 0.5;
  const empty = 5 - full - (half ? 1 : 0);

  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: "2px" }}>
      {Array.from({ length: full }).map((_, i) => (
        <span key={`f${i}`} className="star-filled" style={{ fontSize: size }}>
          ★
        </span>
      ))}
      {half && (
        <span className="star-filled" style={{ fontSize: size, opacity: 0.6 }}>
          ★
        </span>
      )}
      {Array.from({ length: empty }).map((_, i) => (
        <span key={`e${i}`} className="star-empty" style={{ fontSize: size }}>
          ★
        </span>
      ))}
      {showNumber && (
        <span
          style={{
            marginLeft: "6px",
            fontSize: size - 1,
            color: "var(--color-text-secondary)",
            fontWeight: 500,
          }}
        >
          {rating.toFixed(1)}
        </span>
      )}
    </div>
  );
}
