"""
Loads chargebacks.csv into a pandas DataFrame and provides filtering utilities.
"""
import os
import pandas as pd
from datetime import date, timedelta
from typing import Optional, List

_df: Optional[pd.DataFrame] = None
_tx_df: Optional[pd.DataFrame] = None

CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "chargebacks.csv")
TX_CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "transactions_daily.csv")


def load_data() -> pd.DataFrame:
    global _df
    if _df is None:
        _df = pd.read_csv(CSV_PATH)
        # Normalize new schema column names to keep the rest of the code stable
        _df["date"] = pd.to_datetime(_df["chargeback_date"]).dt.date
        _df = _df.rename(columns={"category": "reason_category", "amount": "amount_usd"})
    return _df


def load_transactions() -> pd.DataFrame:
    global _tx_df
    if _tx_df is None:
        _tx_df = pd.read_csv(TX_CSV_PATH, parse_dates=["date"])
        _tx_df["date"] = pd.to_datetime(_tx_df["date"]).dt.date
    return _tx_df


def get_df() -> pd.DataFrame:
    return load_data()


def get_tx_df() -> pd.DataFrame:
    return load_transactions()


def apply_filters(
    df: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    merchant_id: Optional[str] = None,
    reason_category: Optional[List[str]] = None,
    payment_method: Optional[List[str]] = None,
    country: Optional[List[str]] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
) -> pd.DataFrame:
    mask = pd.Series([True] * len(df), index=df.index)

    if start_date:
        from dateutil.parser import parse as parse_date
        sd = parse_date(start_date).date()
        mask &= df["date"] >= sd

    if end_date:
        from dateutil.parser import parse as parse_date
        ed = parse_date(end_date).date()
        mask &= df["date"] <= ed

    if merchant_id:
        # Support partial match (search)
        mask &= (
            df["merchant_id"].str.contains(merchant_id, case=False, na=False)
            | df["merchant_name"].str.contains(merchant_id, case=False, na=False)
        )

    if reason_category:
        mask &= df["reason_category"].isin(reason_category)

    if payment_method:
        mask &= df["payment_method"].isin(payment_method)

    if country:
        mask &= df["country"].isin(country)

    if min_amount is not None:
        mask &= df["amount_usd"] >= min_amount

    if max_amount is not None:
        mask &= df["amount_usd"] <= max_amount

    return df[mask].copy()


def compute_trend_pct(
    df: pd.DataFrame,
    start_date: Optional[str],
    end_date: Optional[str],
) -> float:
    """
    Compare chargeback count in the current period vs the same-length previous period.
    Returns percentage change (positive = worsening).
    """
    from dateutil.parser import parse as parse_date

    if not start_date or not end_date:
        today = date.today()
        ed = today
        sd = today - timedelta(days=29)
    else:
        sd = parse_date(start_date).date()
        ed = parse_date(end_date).date()

    period_len = (ed - sd).days
    prev_sd = sd - timedelta(days=period_len + 1)
    prev_ed = sd - timedelta(days=1)

    current_count = len(df[(df["date"] >= sd) & (df["date"] <= ed)])
    prev_df = get_df()
    prev_count = len(prev_df[(prev_df["date"] >= prev_sd) & (prev_df["date"] <= prev_ed)])

    if prev_count == 0:
        return 0.0

    return round((current_count - prev_count) / prev_count * 100, 1)


def compute_chargeback_rate(
    chargeback_count: int,
    merchant_ids: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    payment_method: Optional[List[str]] = None,
    country: Optional[List[str]] = None,
) -> float:
    """
    Compute chargeback rate against real transaction volume from transactions_daily.csv.
    Filters are applied consistently: date range, merchant IDs, payment method, country.
    reason_category and amount range are chargeback-specific and not present in transactions.
    """
    from dateutil.parser import parse as parse_date

    tx = load_transactions()
    mask = pd.Series([True] * len(tx), index=tx.index)

    if start_date:
        sd = parse_date(start_date).date()
        mask &= tx["date"] >= sd

    if end_date:
        ed = parse_date(end_date).date()
        mask &= tx["date"] <= ed

    if merchant_ids:
        mask &= tx["merchant_id"].isin(merchant_ids)

    if payment_method:
        mask &= tx["payment_method"].isin(payment_method)

    if country:
        mask &= tx["country"].isin(country)

    total_transactions = int(tx.loc[mask, "transactions_count"].sum())

    if total_transactions == 0 or chargeback_count == 0:
        return 0.0

    return round(chargeback_count / total_transactions * 100, 2)
