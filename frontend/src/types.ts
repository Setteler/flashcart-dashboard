export interface Filters {
  start_date: string;
  end_date: string;
  merchant_id: string;
  reason_category: string[];
  payment_method: string[];
  country: string[];
  min_amount: string;
  max_amount: string;
}

export interface ChargebackRecord {
  chargeback_id: string;
  date: string;
  merchant_id: string;
  merchant_name: string;
  merchant_category: string;
  country: string;
  reason_category: string;
  reason_code: string;
  payment_method: string;
  amount_usd: number;
  status: "open" | "won" | "lost";
}

export interface ChargebacksResponse {
  records: ChargebackRecord[];
  total: number;
  page: number;
  page_size: number;
}

export interface ByCategory {
  category: string;
  count: number;
  amount: number;
}

export interface ByCountry {
  country: string;
  count: number;
  amount: number;
}

export interface ByPaymentMethod {
  payment_method: string;
  count: number;
  amount: number;
}

export interface ByDate {
  date: string;
  count: number;
  amount: number;
}

export interface TopMerchant {
  merchant_id: string;
  merchant_name: string;
  count: number;
  amount: number;
  rate: number;
}

export interface MetricsResponse {
  total_chargebacks: number;
  total_disputed_amount: number;
  chargeback_rate: number;
  trend_pct: number;
  by_category: ByCategory[];
  by_country: ByCountry[];
  by_payment_method: ByPaymentMethod[];
  by_day: ByDate[];
  top_merchants: TopMerchant[];
}
