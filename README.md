# FlashCart Chargeback Intelligence Dashboard

Real-time chargeback monitoring for Southeast Asian e-commerce merchants.
Identify surge drivers across merchants, reason codes, and payment methods
with a filterable dashboard backed by a FastAPI + pandas API.

**Repository:** https://github.com/Setteler/flashcart-dashboard

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| Node.js | 18+ |
| npm | 9+ |

---

## Quick Start

### 1 · Start the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
```

The dataset (`backend/data/chargebacks.csv`, 1,000 rows across 55 merchants) is
pre-committed — no generation step needed.

Interactive API docs: http://localhost:8000/docs

---

### 2 · Start the frontend

Open a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

Vite proxies `/api/*` to `localhost:8000` automatically during development.

---

### (Optional) Regenerate sample data

```bash
python scripts/generate_data.py
```

Recreates `backend/data/chargebacks.csv` (1,000 rows) and
`backend/data/transactions_daily.csv` from a fixed seed (`SEED = 42`).

---

## Architecture

```
flashcart-dashboard/
├── scripts/
│   └── generate_data.py          # Synthetic data generator (optional, deterministic)
├── backend/
│   ├── data/
│   │   ├── chargebacks.csv       # 1,000 chargeback events — 90 days, 55 merchants
│   │   └── transactions_daily.csv# Daily transaction aggregates for real CB-rate calc
│   ├── app.py                    # FastAPI app — /api/metrics, /api/chargebacks, /api/health
│   ├── data_loader.py            # CSV → DataFrame, filter & metric helpers
│   └── requirements.txt
└── frontend/
    └── src/
        ├── App.tsx               # Root shell, filter state, parallel data fetch
        ├── components/           # MetricsBar · TimeSeriesChart · BreakdownChart
        │                         # ChargebackTable · FiltersPanel
        └── api/client.ts         # Typed fetch wrappers (respects VITE_API_BASE_URL)
```

**Data flow:**

```
chargebacks.csv ──────────────────────────────┐
                                               ↓
transactions_daily.csv → pandas DataFrames (loaded at startup)
                                               ↓
                         FastAPI filters / aggregates on request
                                               ↓
                         React components render JSON
```

No database required. The 1,000-row dataset fits entirely in memory.
Chargeback rate is computed as `filtered_chargebacks ÷ filtered_transactions_count`
using the matching slice of `transactions_daily.csv` — rate updates correctly with every filter.

---

## Demo Guide — 3 Filters to Try

### Filter 1 · Fraud Spike Merchant

> Show a single merchant with a sharp fraud uptick in the last 10 days.

1. In the **Merchant** search box type `GamersParadise`
2. Set **Date range** → last 10 days
3. Look at the **Reason breakdown** chart — fraud jumps to ~85% share
4. The **Time-series chart** shows a steep recent uptick against a flat baseline

---

### Filter 2 · Indonesia × GoPay Analysis

> Show payment-method risk segmentation within a single market.

1. Select **Country** → `ID`
2. Select **Payment method** → `gopay`
3. Note the **Chargeback rate** KPI — compare it with `visa` selected instead
4. The **Country breakdown** collapses to Indonesia only; reason split remains

*Indonesia carries 40% of all chargebacks; switching payment methods reveals distinct risk profiles.*

---

### Filter 3 · Product Not Received Deep-Dive

> Show a merchant with a persistent fulfilment failure pattern.

1. Select **Reason category** → `product_not_received`
2. Clear all other filters
3. Scroll to the **Top merchants** table — click any merchant row to drill down
4. All charts and the KPI bar update to show that merchant's 90-day pattern

---

## API Reference

```bash
# Filtered metrics
curl "http://localhost:8000/api/metrics?country=ID&reason_category=fraud"

# Paginated records, sorted by amount
curl "http://localhost:8000/api/chargebacks?page=1&page_size=20&sort_by=amount_usd&sort_dir=desc"

# Single merchant drill-down
curl "http://localhost:8000/api/metrics?merchant_id=M003"

# Health check
curl "http://localhost:8000/api/health"
```

---

## Data Model

| Column | Example |
|--------|---------|
| `chargeback_id` | UUID |
| `chargeback_date` | `2025-12-18T14:23:07` |
| `merchant_id` | `M003` |
| `merchant_name` | `GamersParadise` |
| `merchant_category` | `gaming` |
| `product_name` | `Razer DeathAdder Mouse` |
| `amount` | `74.50` |
| `currency` | `USD` |
| `country` | `ID` / `PH` / `TH` / `VN` |
| `payment_method` | `visa` / `gopay` / `bank_transfer` … |
| `processor` | `Adyen` / `Midtrans` / `Xendit` … |
| `reason_code` | `10.4` |
| `category` | `fraud` / `product_not_received` … |
