import { useState } from "react";
import type { ChargebackRecord, ChargebacksResponse, Filters } from "../types";
import { fetchChargebacks } from "../api/client";

interface Props {
  data: ChargebacksResponse | null;
  loading: boolean;
  filters: Filters;
  onDataChange: (d: ChargebacksResponse) => void;
  onLoadingChange: (v: boolean) => void;
}

const STATUS_COLORS: Record<string, string> = {
  open: "#f59e0b",
  won: "#22c55e",
  lost: "#ef4444",
};

const COLUMNS: { key: keyof ChargebackRecord | ""; label: string; sortable: boolean }[] = [
  { key: "date", label: "Date", sortable: true },
  { key: "merchant_name", label: "Merchant", sortable: true },
  { key: "country", label: "Country", sortable: true },
  { key: "reason_category", label: "Reason", sortable: true },
  { key: "payment_method", label: "Payment", sortable: true },
  { key: "processor", label: "Processor", sortable: true },
  { key: "amount_usd", label: "Amount", sortable: true },
  { key: "status", label: "Status", sortable: true },
];

export default function ChargebackTable({
  data,
  loading,
  filters,
  onDataChange,
  onLoadingChange,
}: Props) {
  const [sortBy, setSortBy] = useState("date");
  const [sortDir, setSortDir] = useState("desc");
  const [search, setSearch] = useState("");

  const handleSort = async (col: string) => {
    const newDir = col === sortBy && sortDir === "desc" ? "asc" : "desc";
    setSortBy(col);
    setSortDir(newDir);
    onLoadingChange(true);
    try {
      const result = await fetchChargebacks(filters, data?.page ?? 1, data?.page_size ?? 50, col, newDir);
      onDataChange(result);
    } finally {
      onLoadingChange(false);
    }
  };

  const handlePage = async (page: number) => {
    onLoadingChange(true);
    try {
      const result = await fetchChargebacks(filters, page, data?.page_size ?? 50, sortBy, sortDir);
      onDataChange(result);
    } finally {
      onLoadingChange(false);
    }
  };

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 1;
  const currentPage = data?.page ?? 1;

  const needle = search.toLowerCase();
  const visibleRecords = search
    ? (data?.records ?? []).filter(
        (r) =>
          r.merchant_name.toLowerCase().includes(needle) ||
          r.reason_category.toLowerCase().includes(needle) ||
          r.country.toLowerCase().includes(needle)
      )
    : data?.records ?? [];

  const thStyle: React.CSSProperties = {
    padding: "10px 12px",
    textAlign: "left",
    fontSize: 11,
    fontWeight: 600,
    color: "#94a3b8",
    textTransform: "uppercase",
    letterSpacing: 0.5,
    borderBottom: "1px solid #334155",
    whiteSpace: "nowrap",
  };

  const tdStyle: React.CSSProperties = {
    padding: "9px 12px",
    fontSize: 13,
    color: "#cbd5e1",
    borderBottom: "1px solid #1e293b",
    whiteSpace: "nowrap",
  };

  return (
    <div
      style={{
        background: "#1e293b",
        borderRadius: 8,
        border: "1px solid #334155",
        overflow: "hidden",
      }}
    >
      <div style={{ padding: "14px 16px", borderBottom: "1px solid #334155", display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
        <span style={{ fontSize: 14, fontWeight: 600, color: "#f1f5f9", whiteSpace: "nowrap" }}>Chargeback Records</span>
        <input
          type="text"
          placeholder="Search merchant, reason, country…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            flex: 1,
            maxWidth: 280,
            background: "#0f172a",
            border: "1px solid #334155",
            borderRadius: 4,
            padding: "5px 10px",
            fontSize: 12,
            color: "#f1f5f9",
            outline: "none",
          }}
        />
        {data && (
          <span style={{ fontSize: 12, color: "#64748b", whiteSpace: "nowrap" }}>
            {data.total.toLocaleString()} records
          </span>
        )}
      </div>

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              {COLUMNS.map((col) => (
                <th
                  key={col.label}
                  style={{
                    ...thStyle,
                    cursor: col.sortable ? "pointer" : "default",
                    userSelect: "none",
                  }}
                  onClick={col.sortable && col.key ? () => handleSort(col.key as string) : undefined}
                >
                  {col.label}
                  {col.sortable && col.key === sortBy ? (sortDir === "desc" ? " ▼" : " ▲") : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={COLUMNS.length} style={{ ...tdStyle, textAlign: "center", color: "#475569", padding: 32 }}>
                  Loading…
                </td>
              </tr>
            ) : visibleRecords.length === 0 ? (
              <tr>
                <td colSpan={COLUMNS.length} style={{ ...tdStyle, textAlign: "center", color: "#475569", padding: 32 }}>
                  No records found
                </td>
              </tr>
            ) : (
              visibleRecords.map((row) => (
                <tr key={row.chargeback_id} style={{ transition: "background 0.1s" }}
                  onMouseEnter={(e) => ((e.currentTarget as HTMLTableRowElement).style.background = "#243347")}
                  onMouseLeave={(e) => ((e.currentTarget as HTMLTableRowElement).style.background = "")}
                >
                  <td style={tdStyle}>{row.date}</td>
                  <td style={tdStyle}>
                    <div style={{ fontWeight: 500, color: "#f1f5f9" }}>{row.merchant_name}</div>
                    <div style={{ fontSize: 11, color: "#475569" }}>{row.merchant_id}</div>
                  </td>
                  <td style={tdStyle}>{row.country}</td>
                  <td style={tdStyle}>
                    <div>{row.reason_category.replace(/_/g, " ")}</div>
                    <div style={{ fontSize: 11, color: "#475569" }}>{row.reason_code}</div>
                  </td>
                  <td style={tdStyle}>
                    <div>{row.payment_method}</div>
                    {row.product_name && (
                      <div style={{ fontSize: 11, color: "#475569", maxWidth: 140, overflow: "hidden", textOverflow: "ellipsis" }}>
                        {row.product_name}
                      </div>
                    )}
                  </td>
                  <td style={tdStyle}>{row.processor}</td>
                  <td style={{ ...tdStyle, fontWeight: 500, color: "#f1f5f9" }}>
                    ${row.amount_usd.toFixed(2)}
                  </td>
                  <td style={tdStyle}>
                    <span
                      style={{
                        display: "inline-block",
                        padding: "2px 8px",
                        borderRadius: 4,
                        fontSize: 12,
                        fontWeight: 600,
                        color: STATUS_COLORS[row.status] ?? "#94a3b8",
                        background: `${STATUS_COLORS[row.status] ?? "#94a3b8"}22`,
                      }}
                    >
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {data && totalPages > 1 && (
        <div
          style={{
            display: "flex",
            gap: 8,
            alignItems: "center",
            justifyContent: "flex-end",
            padding: "12px 16px",
            borderTop: "1px solid #334155",
          }}
        >
          <button
            onClick={() => handlePage(currentPage - 1)}
            disabled={currentPage <= 1}
            style={{
              background: "#334155",
              color: currentPage <= 1 ? "#475569" : "#f1f5f9",
              border: "none",
              borderRadius: 4,
              padding: "5px 12px",
              cursor: currentPage <= 1 ? "not-allowed" : "pointer",
              fontSize: 13,
            }}
          >
            ‹ Prev
          </button>
          <span style={{ fontSize: 13, color: "#94a3b8" }}>
            Page {currentPage} / {totalPages}
          </span>
          <button
            onClick={() => handlePage(currentPage + 1)}
            disabled={currentPage >= totalPages}
            style={{
              background: "#334155",
              color: currentPage >= totalPages ? "#475569" : "#f1f5f9",
              border: "none",
              borderRadius: 4,
              padding: "5px 12px",
              cursor: currentPage >= totalPages ? "not-allowed" : "pointer",
              fontSize: 13,
            }}
          >
            Next ›
          </button>
        </div>
      )}
    </div>
  );
}
