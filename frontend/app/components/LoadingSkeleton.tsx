// Reusable loading skeleton components

export function BookCardSkeleton() {
  return (
    <div
      className="glass-card"
      style={{ overflow: "hidden", display: "flex", flexDirection: "column" }}
    >
      {/* Cover skeleton */}
      <div
        className="skeleton"
        style={{ width: "100%", aspectRatio: "2/3", borderRadius: "10px 10px 0 0" }}
      />

      {/* Content skeletons */}
      <div style={{ padding: "14px", display: "flex", flexDirection: "column", gap: "10px" }}>
        <div className="skeleton" style={{ height: "16px", width: "50%", borderRadius: "4px" }} />
        <div className="skeleton" style={{ height: "14px", width: "90%", borderRadius: "4px" }} />
        <div className="skeleton" style={{ height: "14px", width: "70%", borderRadius: "4px" }} />
        <div className="skeleton" style={{ height: "12px", width: "40%", borderRadius: "4px" }} />
      </div>
    </div>
  );
}

export function BookGridSkeleton({ count = 12 }: { count?: number }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
        gap: "20px",
      }}
    >
      {Array.from({ length: count }).map((_, i) => (
        <BookCardSkeleton key={i} />
      ))}
    </div>
  );
}

export function BookDetailSkeleton() {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: "32px" }}>
      {/* Left col */}
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <div className="skeleton" style={{ width: "100%", aspectRatio: "2/3", borderRadius: "12px" }} />
        <div className="skeleton" style={{ height: "20px", width: "80%" }} />
        <div className="skeleton" style={{ height: "16px", width: "60%" }} />
      </div>
      {/* Right col */}
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <div className="skeleton" style={{ height: "32px", width: "70%" }} />
        <div className="skeleton" style={{ height: "16px", width: "40%" }} />
        {[1, 2, 3].map((i) => (
          <div key={i} className="skeleton" style={{ height: "80px", borderRadius: "12px" }} />
        ))}
      </div>
    </div>
  );
}

export function StatCardSkeleton() {
  return (
    <div className="glass-card" style={{ padding: "20px" }}>
      <div className="skeleton" style={{ height: "28px", width: "50%", marginBottom: "8px" }} />
      <div className="skeleton" style={{ height: "16px", width: "70%" }} />
    </div>
  );
}
