import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { ByCategory, ByPaymentMethod, ByCountry } from "../types";

const COLORS = ["#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6", "#10b981", "#f97316", "#ec4899"];

interface Props {
  byReason: ByCategory[];
  byPayment: ByPaymentMethod[];
  byCountry: ByCountry[];
  loading: boolean;
}

function SmallBar({
  title,
  data,
  nameKey,
}: {
  title: string;
  data: Array<{ name: string; count: number }>;
  nameKey: string;
}) {
  return (
    <div
      style={{
        background: "#1e293b",
        borderRadius: 8,
        padding: "16px",
        border: "1px solid #334155",
        flex: 1,
        minWidth: 260,
      }}
    >
      <div style={{ fontSize: 13, fontWeight: 600, color: "#f1f5f9", marginBottom: 12 }}>{title}</div>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 24, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
          <XAxis type="number" tick={{ fill: "#64748b", fontSize: 11 }} allowDecimals={false} />
          <YAxis
            type="category"
            dataKey={nameKey}
            width={110}
            tick={{ fill: "#94a3b8", fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 6 }}
            labelStyle={{ color: "#94a3b8" }}
            itemStyle={{ color: "#f1f5f9" }}
          />
          <Bar dataKey="count" radius={[0, 4, 4, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function BreakdownChart({ byReason, byPayment, byCountry, loading }: Props) {
  const reasonData = byReason
    .map((r) => ({ name: r.category, count: r.count }))
    .sort((a, b) => b.count - a.count);

  const paymentData = byPayment
    .map((p) => ({ name: p.payment_method, count: p.count }))
    .sort((a, b) => b.count - a.count);

  const countryData = byCountry
    .map((c) => ({ name: c.country, count: c.count }))
    .sort((a, b) => b.count - a.count);

  if (loading) {
    return (
      <div style={{ display: "flex", gap: 16, marginBottom: 20 }}>
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            style={{ flex: 1, minWidth: 260, height: 230, background: "#1e293b", borderRadius: 8 }}
          />
        ))}
      </div>
    );
  }

  return (
    <div style={{ display: "flex", gap: 16, marginBottom: 20, flexWrap: "wrap" }}>
      <SmallBar title="By Reason Category" data={reasonData} nameKey="name" />
      <SmallBar title="By Payment Method" data={paymentData} nameKey="name" />
      <SmallBar title="By Country" data={countryData} nameKey="name" />
    </div>
  );
}
