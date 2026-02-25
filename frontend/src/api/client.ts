import type { Filters, ChargebacksResponse, MetricsResponse } from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

function buildQuery(filters: Filters, extra: Record<string, string | number> = {}): string {
  const params = new URLSearchParams();

  if (filters.start_date) params.set("start_date", filters.start_date);
  if (filters.end_date) params.set("end_date", filters.end_date);
  if (filters.merchant_id) params.set("merchant_id", filters.merchant_id);
  if (filters.reason_category.length > 0)
    params.set("reason_category", filters.reason_category.join(","));
  if (filters.payment_method.length > 0)
    params.set("payment_method", filters.payment_method.join(","));
  if (filters.country.length > 0) params.set("country", filters.country.join(","));
  if (filters.min_amount) params.set("min_amount", filters.min_amount);
  if (filters.max_amount) params.set("max_amount", filters.max_amount);

  for (const [key, value] of Object.entries(extra)) {
    params.set(key, String(value));
  }

  return params.toString();
}

export async function fetchMetrics(filters: Filters): Promise<MetricsResponse> {
  const qs = buildQuery(filters);
  const res = await fetch(`${BASE_URL}/api/metrics?${qs}`);
  if (!res.ok) throw new Error(`Metrics fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchChargebacks(
  filters: Filters,
  page = 1,
  pageSize = 50,
  sortBy = "date",
  sortDir = "desc"
): Promise<ChargebacksResponse> {
  const qs = buildQuery(filters, {
    page,
    page_size: pageSize,
    sort_by: sortBy,
    sort_dir: sortDir,
  });
  const res = await fetch(`${BASE_URL}/api/chargebacks?${qs}`);
  if (!res.ok) throw new Error(`Chargebacks fetch failed: ${res.status}`);
  return res.json();
}
