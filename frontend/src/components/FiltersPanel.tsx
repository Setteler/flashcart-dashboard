import { useState } from "react";
import type { Filters } from "../types";

const REASON_CATEGORIES = [
  "fraud",
  "product_not_received",
  "product_not_as_described",
  "duplicate_processing",
  "subscription_cancelled",
];

const PAYMENT_METHODS = ["visa", "mastercard", "gopay", "ovo", "gcash", "truemoney", "bank_transfer"];
const COUNTRIES = ["ID", "PH", "TH", "VN"];

interface Props {
  filters: Filters;
  onApply: (f: Filters) => void;
}

function MultiCheckbox({
  label,
  options,
  selected,
  onChange,
}: {
  label: string;
  options: string[];
  selected: string[];
  onChange: (v: string[]) => void;
}) {
  const toggle = (opt: string) => {
    if (selected.includes(opt)) {
      onChange(selected.filter((s) => s !== opt));
    } else {
      onChange([...selected, opt]);
    }
  };

  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 11, color: "#94a3b8", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
        {options.map((opt) => (
          <label
            key={opt}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 4,
              cursor: "pointer",
              background: selected.includes(opt) ? "#3b82f6" : "#334155",
              borderRadius: 4,
              padding: "3px 8px",
              fontSize: 12,
              color: selected.includes(opt) ? "#fff" : "#cbd5e1",
              userSelect: "none",
            }}
          >
            <input
              type="checkbox"
              checked={selected.includes(opt)}
              onChange={() => toggle(opt)}
              style={{ display: "none" }}
            />
            {opt}
          </label>
        ))}
      </div>
    </div>
  );
}

export default function FiltersPanel({ filters, onApply }: Props) {
  const [local, setLocal] = useState<Filters>({ ...filters });

  const update = <K extends keyof Filters>(key: K, value: Filters[K]) => {
    setLocal((prev) => ({ ...prev, [key]: value }));
  };

  const handleReset = () => {
    const today = new Date().toISOString().slice(0, 10);
    const d30 = new Date(Date.now() - 29 * 86400000).toISOString().slice(0, 10);
    const reset: Filters = {
      start_date: d30,
      end_date: today,
      merchant_id: "",
      reason_category: [],
      payment_method: [],
      country: [],
      min_amount: "",
      max_amount: "",
    };
    setLocal(reset);
    onApply(reset);
  };

  const inputStyle: React.CSSProperties = {
    background: "#334155",
    border: "1px solid #475569",
    borderRadius: 4,
    color: "#f1f5f9",
    padding: "5px 8px",
    fontSize: 13,
    width: "100%",
    boxSizing: "border-box",
  };

  const labelStyle: React.CSSProperties = {
    fontSize: 11,
    color: "#94a3b8",
    textTransform: "uppercase",
    letterSpacing: 1,
    display: "block",
    marginBottom: 4,
  };

  return (
    <div
      style={{
        background: "#1e293b",
        borderRadius: 8,
        padding: 20,
        marginBottom: 24,
        border: "1px solid #334155",
      }}
    >
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 16 }}>
        {/* Date range */}
        <div>
          <label style={labelStyle}>Start Date</label>
          <input
            type="date"
            value={local.start_date}
            onChange={(e) => update("start_date", e.target.value)}
            style={inputStyle}
          />
        </div>
        <div>
          <label style={labelStyle}>End Date</label>
          <input
            type="date"
            value={local.end_date}
            onChange={(e) => update("end_date", e.target.value)}
            style={inputStyle}
          />
        </div>

        {/* Merchant search */}
        <div>
          <label style={labelStyle}>Merchant Search</label>
          <input
            type="text"
            placeholder="ID or name…"
            value={local.merchant_id}
            onChange={(e) => update("merchant_id", e.target.value)}
            style={inputStyle}
          />
        </div>

        {/* Amount range */}
        <div>
          <label style={labelStyle}>Min Amount ($)</label>
          <input
            type="number"
            placeholder="0"
            value={local.min_amount}
            onChange={(e) => update("min_amount", e.target.value)}
            style={inputStyle}
            min={0}
          />
        </div>
        <div>
          <label style={labelStyle}>Max Amount ($)</label>
          <input
            type="number"
            placeholder="450"
            value={local.max_amount}
            onChange={(e) => update("max_amount", e.target.value)}
            style={inputStyle}
            min={0}
          />
        </div>
      </div>

      {/* Multi-selects */}
      <div style={{ marginTop: 16 }}>
        <MultiCheckbox
          label="Reason Category"
          options={REASON_CATEGORIES}
          selected={local.reason_category}
          onChange={(v) => update("reason_category", v)}
        />
        <MultiCheckbox
          label="Payment Method"
          options={PAYMENT_METHODS}
          selected={local.payment_method}
          onChange={(v) => update("payment_method", v)}
        />
        <MultiCheckbox
          label="Country"
          options={COUNTRIES}
          selected={local.country}
          onChange={(v) => update("country", v)}
        />
      </div>

      {/* Action buttons */}
      <div style={{ display: "flex", gap: 10, marginTop: 4 }}>
        <button
          onClick={() => onApply(local)}
          style={{
            background: "#3b82f6",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            padding: "8px 20px",
            cursor: "pointer",
            fontWeight: 600,
            fontSize: 14,
          }}
        >
          Apply Filters
        </button>
        <button
          onClick={handleReset}
          style={{
            background: "#334155",
            color: "#94a3b8",
            border: "1px solid #475569",
            borderRadius: 6,
            padding: "8px 20px",
            cursor: "pointer",
            fontSize: 14,
          }}
        >
          Reset
        </button>
      </div>
    </div>
  );
}
