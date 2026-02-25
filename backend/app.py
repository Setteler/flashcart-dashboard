"""
FastAPI backend for FlashCart Chargeback Intelligence Dashboard.
"""
import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pandas as pd

from data_loader import (
    get_df,
    apply_filters,
    compute_trend_pct,
    compute_chargeback_rate,
    load_data,
    load_transactions,
)

app = FastAPI(title="FlashCart Chargeback API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    load_data()
    load_transactions()
    print("Data loaded successfully.")


def _parse_list(value: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated query param into a list."""
    if not value:
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


@app.get("/api/chargebacks")
def get_chargebacks(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    merchant_id: Optional[str] = Query(None),
    reason_category: Optional[str] = Query(None),
    payment_method: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    sort_by: Optional[str] = Query(None),
    sort_dir: str = Query("desc"),
) -> Dict[str, Any]:
    df = get_df()
    filtered = apply_filters(
        df,
        start_date=start_date,
        end_date=end_date,
        merchant_id=merchant_id,
        reason_category=_parse_list(reason_category),
        payment_method=_parse_list(payment_method),
        country=_parse_list(country),
        min_amount=min_amount,
        max_amount=max_amount,
    )

    # Sort
    valid_sort_cols = [
        "date", "merchant_name", "merchant_id", "country",
        "reason_category", "payment_method", "amount_usd", "processor",
    ]
    if sort_by and sort_by in valid_sort_cols:
        ascending = sort_dir.lower() != "desc"
        filtered = filtered.sort_values(sort_by, ascending=ascending)
    else:
        filtered = filtered.sort_values("date", ascending=False)

    total = len(filtered)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_df = filtered.iloc[start_idx:end_idx]

    records = page_df.assign(date=page_df["date"].astype(str)).to_dict(orient="records")

    return {
        "records": records,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@app.get("/api/metrics")
def get_metrics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    merchant_id: Optional[str] = Query(None),
    reason_category: Optional[str] = Query(None),
    payment_method: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
) -> Dict[str, Any]:
    df = get_df()
    filtered = apply_filters(
        df,
        start_date=start_date,
        end_date=end_date,
        merchant_id=merchant_id,
        reason_category=_parse_list(reason_category),
        payment_method=_parse_list(payment_method),
        country=_parse_list(country),
        min_amount=min_amount,
        max_amount=max_amount,
    )

    total_chargebacks = len(filtered)
    total_amount = round(float(filtered["amount_usd"].sum()), 2) if total_chargebacks > 0 else 0.0
    filtered_merchant_ids = filtered["merchant_id"].unique().tolist() if total_chargebacks > 0 else None
    chargeback_rate = compute_chargeback_rate(
        total_chargebacks,
        merchant_ids=filtered_merchant_ids,
        start_date=start_date,
        end_date=end_date,
        payment_method=_parse_list(payment_method),
        country=_parse_list(country),
    )
    trend_pct = compute_trend_pct(df, start_date, end_date)

    # By reason
    by_reason = []
    if total_chargebacks > 0:
        reason_grp = (
            filtered.groupby("reason_category")
            .agg(count=("chargeback_id", "count"), amount=("amount_usd", "sum"))
            .reset_index()
        )
        by_reason = [
            {
                "category": row["reason_category"],
                "count": int(row["count"]),
                "amount": round(float(row["amount"]), 2),
            }
            for _, row in reason_grp.iterrows()
        ]

    # By country
    by_country = []
    if total_chargebacks > 0:
        country_grp = (
            filtered.groupby("country")
            .agg(count=("chargeback_id", "count"), amount=("amount_usd", "sum"))
            .reset_index()
        )
        by_country = [
            {
                "country": row["country"],
                "count": int(row["count"]),
                "amount": round(float(row["amount"]), 2),
            }
            for _, row in country_grp.iterrows()
        ]

    # By payment method
    by_payment_method = []
    if total_chargebacks > 0:
        pm_grp = (
            filtered.groupby("payment_method")
            .agg(count=("chargeback_id", "count"), amount=("amount_usd", "sum"))
            .reset_index()
        )
        by_payment_method = [
            {
                "payment_method": row["payment_method"],
                "count": int(row["count"]),
                "amount": round(float(row["amount"]), 2),
            }
            for _, row in pm_grp.iterrows()
        ]

    # By processor
    by_processor = []
    if total_chargebacks > 0:
        proc_grp = (
            filtered.groupby("processor")
            .agg(count=("chargeback_id", "count"), amount=("amount_usd", "sum"))
            .reset_index()
        )
        by_processor = [
            {
                "processor": row["processor"],
                "count": int(row["count"]),
                "amount": round(float(row["amount"]), 2),
            }
            for _, row in proc_grp.iterrows()
        ]

    # By date (daily)
    by_date = []
    if total_chargebacks > 0:
        date_grp = (
            filtered.groupby("date")
            .agg(count=("chargeback_id", "count"), amount=("amount_usd", "sum"))
            .reset_index()
            .sort_values("date")
        )
        by_date = [
            {
                "date": str(row["date"]),
                "count": int(row["count"]),
                "amount": round(float(row["amount"]), 2),
            }
            for _, row in date_grp.iterrows()
        ]

    # Top merchants
    top_merchants = []
    if total_chargebacks > 0:
        merch_grp = (
            filtered.groupby(["merchant_id", "merchant_name"])
            .agg(count=("chargeback_id", "count"), amount=("amount_usd", "sum"))
            .reset_index()
            .sort_values("count", ascending=False)
            .head(10)
        )
        for _, row in merch_grp.iterrows():
            merch_count = int(row["count"])
            top_merchants.append(
                {
                    "merchant_id": row["merchant_id"],
                    "merchant_name": row["merchant_name"],
                    "count": merch_count,
                    "amount": round(float(row["amount"]), 2),
                    "rate": compute_chargeback_rate(
                        merch_count,
                        merchant_ids=[row["merchant_id"]],
                        start_date=start_date,
                        end_date=end_date,
                        payment_method=_parse_list(payment_method),
                        country=_parse_list(country),
                    ),
                }
            )

    return {
        "total_chargebacks": total_chargebacks,
        "total_disputed_amount": total_amount,
        "chargeback_rate": chargeback_rate,
        "trend_pct": trend_pct,
        "by_category": by_reason,
        "by_country": by_country,
        "by_payment_method": by_payment_method,
        "by_processor": by_processor,
        "by_day": by_date,
        "top_merchants": top_merchants,
    }


@app.get("/api/health")
def health() -> Dict[str, Any]:
    df = get_df()
    return {"status": "ok", "version": "1.0.0", "records_loaded": len(df)}


# Serve React frontend in production (when dist/ exists)
_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(_dist, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        return FileResponse(os.path.join(_dist, "index.html"))
