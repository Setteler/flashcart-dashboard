# FlashCart Chargeback Intelligence Dashboard

Real-time chargeback monitoring for Southeast Asian e-commerce merchants.
Identify surge drivers across merchants, reason codes, and payment methods
with a filterable dashboard backed by a FastAPI + Pandas API.

**Live demo:** _see deployed URLs below_

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| Node.js | 18+ |
| npm | 9+ |

---

## Quick Start (local)

### 1 · Start the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Sample data (`backend/chargebacks.csv`, 910 rows) is pre-committed — no generation step needed.

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

Vite proxies `/api/*` to `localhost:8000` automatically during dev.

---

### (Optional) Regenerate sample data

Run from the `backend/` directory to recreate both CSVs from scratch:

```bash
cd backend
python generate_data.py
```

Regenerates `backend/chargebacks.csv` (910 chargeback rows) and `backend/data/transactions_daily.csv`.

---

## Architecture

```
flashcart-dashboard/
├── render.yaml                       # Render deployment config (backend)
├── scripts/
│   └── generate_data.py              # Synthetic data generator (optional)
├── backend/
│   ├── chargebacks.csv               # 910 chargeback rows (pre-generated)
│   ├── main.py                       # FastAPI app — /api/metrics, /api/chargebacks
│   ├── data_loader.py                # CSV → DataFrame, filter & metric helpers
│   └── requirements.txt
└── frontend/
    ├── .env.example                  # Environment variable template
    └── src/
        ├── App.tsx                   # Root shell, filter state, parallel data fetch
        ├── components/               # MetricsBar · TimeSeriesChart · BreakdownChart
        │                             # ChargebackTable · FiltersPanel
        └── api/client.ts             # Typed fetch wrappers (respects VITE_API_BASE_URL)
```

**Data flow:**

```
chargebacks.csv → pandas DataFrame (loaded at startup)
                        ↓
              FastAPI filters / aggregates on request
                        ↓
              React components render JSON
```

No database required. The ~910-row dataset fits entirely in memory.

---

## Demo Guide — 3 Filters to Try

### Filter 1 · Fraud Spike Merchant

> Show a single merchant with a sharp fraud uptick in the last 10 days.

1. In the **Merchant** search box type `GamersParadise`
2. Set **Date range** → last 10 days
3. Look at the **Reason breakdown** chart — fraud jumps to ~85% share
4. The **Time-series chart** shows a steep recent uptick against a flat baseline

*Data pattern:* 72% of all chargebacks are concentrated in merchants M001–M008, so these merchants dominate the recent surge window. Fraud is the top reason category overall (~40% share).

---

### Filter 2 · Indonesia × GoPay Analysis

> Show payment-method risk segmentation within a single market.

1. Select **Country** → `ID`
2. Select **Payment method** → `gopay`
3. Note the **Chargeback rate** KPI — compare it with `visa` selected instead
4. The **Country breakdown** collapses to Indonesia only; reason split remains

*Data pattern:* Indonesia carries 40% of all chargebacks; GoPay is the dominant local e-wallet.

---

### Filter 3 · Product Not Received Deep-Dive

> Show a merchant with a persistent fulfilment failure pattern.

1. Select **Reason category** → `product_not_received`
2. Clear all other filters
3. Scroll to the **Top merchants** table — ElectroShop VN (M006) sits at #1
4. Click into M006 to confirm the pattern holds across the full 90-day window

*Data pattern:* `product_not_received` accounts for ~30% of all chargebacks. The top merchant by this reason will be one of M001–M008, which collectively receive 72% of total volume.

---

## API Quick Reference

```bash
# Metrics with filters
curl "http://localhost:8000/api/metrics?country=ID&reason_category=fraud"

# Paginated chargeback records
curl "http://localhost:8000/api/chargebacks?page=2&page_size=20&sort_by=amount_usd&sort_dir=desc"

# Single merchant drill-down
curl "http://localhost:8000/api/metrics?merchant_id=M003"
```

---

## Deployment

### Backend → Render

1. Connect this repo in [Render](https://render.com) → **New Web Service**
2. Render picks up `render.yaml` automatically (rootDir: `backend`, start: `uvicorn main:app --host 0.0.0.0 --port $PORT`)
3. Copy the deployed URL (e.g. `https://flashcart-backend.onrender.com`)

### Frontend → Vercel

1. Import this repo in [Vercel](https://vercel.com) → set **Root Directory** to `frontend`
2. Add environment variable: `VITE_API_BASE_URL` = `https://flashcart-backend.onrender.com`
3. Deploy — Vercel auto-runs `npm run build` and serves `dist/`

---

## Data Model — `chargebacks.csv`

| Column | Example |
|--------|---------|
| `chargeback_id` | `3f8a1b…` (UUID) |
| `date` | `2025-12-18` |
| `merchant_id` | `M003` |
| `merchant_name` | `GamersParadise` |
| `merchant_category` | `gaming` |
| `country` | `ID` / `PH` / `TH` / `VN` |
| `reason_category` | `fraud` / `product_not_received` / … |
| `reason_code` | `10.4` |
| `payment_method` | `visa` / `gopay` / `bank_transfer` … |
| `amount_usd` | `74.50` |
| `status` | `open` / `won` / `lost` |
