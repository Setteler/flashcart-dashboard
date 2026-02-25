import type { MetricsResponse } from "../types";

interface Props {
  metrics: MetricsResponse | null;
  loading: boolean;
}

function KPICard({
  label,
  value,
  sub,
  highlight,
}: {
  label: string;
  value: string;
  sub?: string;
  highlight?: "red" | "green" | "neutral";
}) {
  const colors: Record<string, string> = {
    red: "#ef4444",
    green: "#22c55e",
    neutral: "#94a3b8",
  };
  const color = highlight ? colors[highlight] : "#f1f5f9";

  return (
    <div
      style={{
        background: "#1e293b",
        border: `1px solid ${color}`,
        borderRadius: 8,
        padding: "16px 20px",
        flex: 1,
        minWidth: 160,
      }}
    >
      <div style={{ fontSize: 12, color: "#94a3b8", textTransform: "uppercase", letterSpacing: 1 }}>
        {label}
      </div>
      <div style={{ fontSize: 28, fontWeight: 700, color, marginTop: 4 }}>{value}</div>
      {sub && <div style={{ fontSize: 12, color: "#64748b", marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

export default function MetricsBar({ metrics, loading }: Props) {
  if (loading || !metrics) {
    return (
      <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            style={{
              flex: 1,
              height: 88,
              background: "#1e293b",
              borderRadius: 8,
              animation: "pulse 1.5s infinite",
            }}
          />
        ))}
      </div>
    );
  }

  const trendDir = metrics.trend_pct > 0 ? "▲" : metrics.trend_pct < 0 ? "▼" : "—";
  const trendHighlight =
    metrics.trend_pct > 0 ? "red" : metrics.trend_pct < 0 ? "green" : "neutral";

  return (
    <div style={{ display: "flex", gap: 12, marginBottom: 24, flexWrap: "wrap" }}>
      <KPICard
        label="Chargeback Rate"
        value={`${metrics.chargeback_rate.toFixed(2)}%`}
        sub="vs ~37× transaction volume"
        highlight={metrics.chargeback_rate > 1.5 ? "red" : "green"}
      />
      <KPICard
        label="Total Chargebacks"
        value={metrics.total_chargebacks.toLocaleString()}
        sub="in selected period"
        highlight="neutral"
      />
      <KPICard
        label="Total Amount"
        value={`$${metrics.total_disputed_amount.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
        sub="USD disputed"
        highlight="neutral"
      />
      <KPICard
        label="Period Trend"
        value={`${trendDir} ${Math.abs(metrics.trend_pct)}%`}
        sub="vs previous same-length period"
        highlight={trendHighlight}
      />
    </div>
  );
}
