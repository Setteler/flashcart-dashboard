import { useState, useEffect, useCallback } from "react";
import type { Filters, MetricsResponse, ChargebacksResponse } from "./types";
import { fetchMetrics, fetchChargebacks } from "./api/client";
import MetricsBar from "./components/MetricsBar";
import FiltersPanel from "./components/FiltersPanel";
import TimeSeriesChart from "./components/TimeSeriesChart";
import BreakdownChart from "./components/BreakdownChart";
import ChargebackTable from "./components/ChargebackTable";

function today(): string {
  return new Date().toISOString().slice(0, 10);
}
function daysMinus(n: number): string {
  return new Date(Date.now() - n * 86400000).toISOString().slice(0, 10);
}

const DEFAULT_FILTERS: Filters = {
  start_date: daysMinus(29),
  end_date: today(),
  merchant_id: "",
  reason_category: [],
  payment_method: [],
  country: [],
  min_amount: "",
  max_amount: "",
};

export default function App() {
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [chargebacks, setChargebacks] = useState<ChargebacksResponse | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(true);
  const [tableLoading, setTableLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAll = useCallback(async (f: Filters) => {
    setMetricsLoading(true);
    setTableLoading(true);
    setError(null);
    try {
      const [m, c] = await Promise.all([
        fetchMetrics(f),
        fetchChargebacks(f, 1, 50, "date", "desc"),
      ]);
      setMetrics(m);
      setChargebacks(c);
    } catch (err) {
      console.error("Failed to load data:", err);
      setError("Failed to load dashboard data. Make sure the backend is running on port 8000.");
    } finally {
      setMetricsLoading(false);
      setTableLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAll(filters);
  }, []);

  const handleApply = (f: Filters) => {
    setFilters(f);
    loadAll(f);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#0f172a",
        color: "#f1f5f9",
        fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif",
        padding: "24px 32px",
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: 24, borderBottom: "1px solid #1e293b", paddingBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0, color: "#f1f5f9" }}>
            FlashCart
          </h1>
          <span style={{ fontSize: 14, color: "#3b82f6", fontWeight: 600 }}>
            Chargeback Intelligence
          </span>
        </div>
        <p style={{ margin: "4px 0 0", fontSize: 13, color: "#64748b" }}>
          Identifying surge drivers across merchants, reason codes, and payment methods
        </p>
      </div>

      {/* Error Banner */}
      {error && (
        <div
          style={{
            background: "#ef444422",
            border: "1px solid #ef4444",
            borderRadius: 6,
            padding: "10px 16px",
            marginBottom: 16,
            fontSize: 13,
            color: "#ef4444",
          }}
        >
          {error}
        </div>
      )}

      {/* KPI Bar */}
      <MetricsBar metrics={metrics} loading={metricsLoading} />

      {/* Filters */}
      <FiltersPanel filters={filters} onApply={handleApply} />

      {/* Time Series */}
      <TimeSeriesChart
        data={metrics?.by_day ?? []}
        loading={metricsLoading}
      />

      {/* Breakdown Charts */}
      <BreakdownChart
        byReason={metrics?.by_category ?? []}
        byPayment={metrics?.by_payment_method ?? []}
        byCountry={metrics?.by_country ?? []}
        loading={metricsLoading}
      />

      {/* Top Merchants */}
      {metrics && metrics.top_merchants.length > 0 && (
        <div
          style={{
            background: "#1e293b",
            borderRadius: 8,
            padding: "16px",
            border: "1px solid #334155",
            marginBottom: 20,
          }}
        >
          <div style={{ fontSize: 14, fontWeight: 600, color: "#f1f5f9", marginBottom: 12 }}>
            Top Merchants by Chargebacks
          </div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  {["Merchant", "ID", "Chargebacks", "Amount (USD)", "CB Rate"].map((h) => (
                    <th
                      key={h}
                      style={{
                        textAlign: "left",
                        padding: "8px 12px",
                        fontSize: 11,
                        fontWeight: 600,
                        color: "#94a3b8",
                        textTransform: "uppercase",
                        letterSpacing: 0.5,
                        borderBottom: "1px solid #334155",
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {metrics.top_merchants.map((m, i) => (
                  <tr key={m.merchant_id}>
                    <td style={{ padding: "8px 12px", fontSize: 13, color: "#f1f5f9", borderBottom: "1px solid #243347" }}>
                      <span style={{ marginRight: 8, color: "#475569", fontSize: 12 }}>{i + 1}.</span>
                      {m.merchant_name}
                    </td>
                    <td style={{ padding: "8px 12px", fontSize: 12, color: "#64748b", borderBottom: "1px solid #243347" }}>
                      {m.merchant_id}
                    </td>
                    <td style={{ padding: "8px 12px", fontSize: 13, fontWeight: 600, color: "#ef4444", borderBottom: "1px solid #243347" }}>
                      {m.count.toLocaleString()}
                    </td>
                    <td style={{ padding: "8px 12px", fontSize: 13, color: "#cbd5e1", borderBottom: "1px solid #243347" }}>
                      ${m.amount.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td style={{ padding: "8px 12px", borderBottom: "1px solid #243347" }}>
                      <span
                        style={{
                          fontSize: 12,
                          fontWeight: 700,
                          color: m.rate > 2 ? "#ef4444" : "#f59e0b",
                          background: m.rate > 2 ? "#ef444422" : "#f59e0b22",
                          padding: "2px 8px",
                          borderRadius: 4,
                        }}
                      >
                        {m.rate.toFixed(2)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Chargeback Table */}
      <ChargebackTable
        data={chargebacks}
        loading={tableLoading}
        filters={filters}
        onDataChange={setChargebacks}
        onLoadingChange={setTableLoading}
      />

      <div style={{ textAlign: "center", marginTop: 32, fontSize: 12, color: "#334155" }}>
        FlashCart Chargeback Intelligence Dashboard · {today()}
      </div>
    </div>
  );
}
