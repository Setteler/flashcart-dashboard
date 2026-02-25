import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { ByDate } from "../types";

interface Props {
  data: ByDate[];
  loading: boolean;
}

export default function TimeSeriesChart({ data, loading }: Props) {
  return (
    <div
      style={{
        background: "#1e293b",
        borderRadius: 8,
        padding: "20px 16px",
        border: "1px solid #334155",
        marginBottom: 20,
      }}
    >
      <div style={{ fontSize: 14, fontWeight: 600, color: "#f1f5f9", marginBottom: 16 }}>
        Daily Chargeback Volume
      </div>
      {loading || data.length === 0 ? (
        <div style={{ height: 220, display: "flex", alignItems: "center", justifyContent: "center", color: "#475569" }}>
          {loading ? "Loading…" : "No data for selected filters"}
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="cbGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="date"
              tick={{ fill: "#64748b", fontSize: 11 }}
              tickFormatter={(d: string) => d.slice(5)}
              interval="preserveStartEnd"
            />
            <YAxis tick={{ fill: "#64748b", fontSize: 11 }} allowDecimals={false} />
            <Tooltip
              contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 6 }}
              labelStyle={{ color: "#94a3b8" }}
              itemStyle={{ color: "#3b82f6" }}
            />
            <Area
              type="monotone"
              dataKey="count"
              stroke="#3b82f6"
              strokeWidth={2}
              fill="url(#cbGrad)"
              name="Chargebacks"
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
