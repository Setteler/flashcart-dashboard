"""
Deterministic synthetic data generator for FlashCart Chargeback Dashboard.

Outputs
-------
backend/data/chargebacks.csv          800–1,200 chargeback rows (last 90 days,
                                      heavier toward recent weeks)
backend/data/transactions_daily.csv   daily transaction aggregates per
                                      date / merchant / country / payment_method /
                                      processor slice – used to compute
                                      chargeback_rate in the API

Run from the project root:
    python scripts/generate_data.py

Requirements: numpy pandas  (already in backend/requirements.txt)
"""

import uuid
import random

import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta
from pathlib import Path

# ─── Reproducibility ─────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# ─── Output paths ─────────────────────────────────────────────────────────────
ROOT         = Path(__file__).resolve().parent.parent
DATA_DIR     = ROOT / "backend" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CHARGEBACKS_OUT  = DATA_DIR / "chargebacks.csv"
TRANSACTIONS_OUT = DATA_DIR / "transactions_daily.csv"

# ─── 90-day date window ───────────────────────────────────────────────────────
TODAY = date.today()
START = TODAY - timedelta(days=89)          # inclusive; 90-day span


def _rand_date(d0: date, d1: date) -> date:
    return d0 + timedelta(days=random.randint(0, (d1 - d0).days))


def _iso_ts(d: date) -> str:
    """Random wall-clock time on *d*, returned as ISO 8601 string."""
    return datetime(
        d.year, d.month, d.day,
        random.randint(0, 23),
        random.randint(0, 59),
        random.randint(0, 59),
    ).isoformat()


# ─── Distribution tables ──────────────────────────────────────────────────────
COUNTRIES  = ["ID", "PH", "TH", "VN"]
COUNTRY_W  = [0.40, 0.25, 0.20, 0.15]

CATEGORIES = [
    "fraud",
    "product_not_received",
    "product_not_as_described",
    "duplicate_processing",
    "subscription_cancelled",
]
CATEGORY_W = [0.40, 0.30, 0.15, 0.08, 0.07]
WEEKEND_W  = [0.58, 0.22, 0.12, 0.05, 0.03]   # fraud surges on Sat/Sun

REASON_CODES = {
    "fraud":                    ["10.4", "10.5", "10.2"],
    "product_not_received":     ["13.1"],
    "product_not_as_described": ["13.3"],
    "duplicate_processing":     ["12.6"],
    "subscription_cancelled":   ["13.2"],
}

# Cards 60 % · e-wallets 30 % · bank transfer 10 %
PAYMENT_METHODS = ["visa", "mastercard", "gopay", "ovo", "gcash", "truemoney", "bank_transfer"]
PAYMENT_W       = [0.37,  0.23,        0.12,   0.10, 0.05,  0.03,       0.10]

PROCESSORS = {
    "visa":          ["Adyen", "Stripe", "Checkout.com"],
    "mastercard":    ["Adyen", "Stripe", "Checkout.com"],
    "gopay":         ["Midtrans"],
    "ovo":           ["Midtrans"],
    "gcash":         ["PayMaya"],
    "truemoney":     ["Omise"],
    "bank_transfer": ["Xendit"],
}

# ─── Merchant catalogue (55 merchants; M001–M008 are "problem" merchants) ─────
MERCH_CATEGORIES = [
    "electronics", "accessories", "gaming", "mobile_phones",
    "fashion", "health_beauty", "home_appliances",
]

MERCHANT_NAMES = [
    # ── Problem merchants M001–M008 ───────────────────────────────────────────
    "TechZone PH", "GadgetHub ID", "GamersParadise", "MobileKing TH",
    "AccessoryWorld", "ElectroShop VN", "QuickGadgets", "PhoneMax ID",
    # ── Normal merchants M009–M055 ────────────────────────────────────────────
    "DigiStore PH", "GamingGear ID", "TechMart VN", "CoolPhone TH",
    "AccessPro ID", "ElectraBuy PH", "SmartGadgets VN", "MobileHub TH",
    "GearUp PH", "TechPulse ID", "GameStop VN", "PhoneZone TH",
    "AccessHub PH", "ElectroMall ID", "SmartStore VN", "MobilePro TH",
    "GadgetPro ID", "TechGo PH", "GameWorld VN", "PhoneMart TH",
    "AccessZone ID", "ElectroGo PH", "SmartHub TH", "MobileZone VN",
    "GadgetStore ID", "TechHub PH", "GameZone VN", "PhoneHub TH",
    "AccessMart PH", "ElectroZone ID", "SmartMart VN", "MobileStore TH",
    "GadgetMall PH", "TechStore ID", "GameHub VN", "PhoneStore TH",
    "AccessStore ID", "ElectroHub PH", "SmartZone VN", "MobileGear TH",
    "GadgetZone PH", "TechMall ID", "GameMart VN", "PhonePro TH",
    "AccessGear ID", "ElectroStore PH", "SmartGear VN",
]
assert len(MERCHANT_NAMES) == 55, f"Expected 55 merchant names, got {len(MERCHANT_NAMES)}"

merchants = [
    {
        "merchant_id":       f"M{i:03d}",
        "merchant_name":     name,
        "merchant_category": random.choice(MERCH_CATEGORIES),
    }
    for i, name in enumerate(MERCHANT_NAMES, start=1)
]

PROBLEM_SET      = {m["merchant_id"] for m in merchants[:8]}  # M001–M008
FRAUD_SPIKE_MID  = "M003"   # GamersParadise  – heavy fraud spike in last 10 days
PNR_STEADY_MID   = "M006"   # ElectroShop VN  – persistent product_not_received

# ─── Product names per merchant category ─────────────────────────────────────
PRODUCTS = {
    "electronics": [
        "Samsung Galaxy S24", "Xiaomi 14 Pro", "OPPO Reno11 5G",
        "Sony WH-1000XM5", "iPad Air M2", "Lenovo Tab P12",
        'LG 55" OLED TV', "Dell Inspiron 15",
    ],
    "accessories": [
        "USB-C 65W Fast Charger", "Screen Protector 3-Pack",
        "Slim Phone Case", "TWS Bluetooth Earbuds",
        "Laptop Sleeve 15\"", "Smart Watch Band Set",
    ],
    "gaming": [
        "PlayStation Store $50 Gift Card", "Xbox Game Pass 3-Month",
        "Razer DeathAdder Mouse", "SteelSeries Arctis Headset",
        "Nintendo Switch Carry Case",
    ],
    "mobile_phones": [
        "iPhone 15 Pro", "Samsung Galaxy A54",
        "Xiaomi Redmi Note 13", "OPPO A78 5G", "Vivo V29",
    ],
    "fashion": [
        "Premium Cotton T-Shirt 3-Pack", "Casual Slip-On Sneakers",
        "UV400 Polarised Sunglasses", "Genuine Leather Wallet",
    ],
    "health_beauty": [
        "Vitamin C Brightening Serum", "Gentle Foam Cleanser Set",
        "Whey Protein Powder 1 kg", "Aromatherapy Essential Oil Kit",
    ],
    "home_appliances": [
        "Smart WiFi Plug 4-Pack", "Compact Air Purifier H13",
        "Rice Cooker 1.8 L", "Touch-Dimmer LED Desk Lamp",
    ],
}


# ─── Helpers ─────────────────────────────────────────────────────────────────
def _pick_category(merchant_id: str, d: date) -> str:
    """Pick reason category with built-in patterns."""
    # Pattern 1 – fraud spike: M003 last 10 days → 85 % fraud
    if merchant_id == FRAUD_SPIKE_MID and (TODAY - d).days <= 10:
        return random.choices(CATEGORIES, weights=[0.85, 0.05, 0.05, 0.03, 0.02])[0]
    # Pattern 2 – consistent PNR: M006 → 88 % product_not_received
    if merchant_id == PNR_STEADY_MID:
        return random.choices(CATEGORIES, weights=[0.05, 0.88, 0.04, 0.02, 0.01])[0]
    # Pattern 3 – weekend fraud surge: fraud probability lifts from 40 % to 58 %
    if d.weekday() >= 5:
        return random.choices(CATEGORIES, weights=WEEKEND_W)[0]
    return random.choices(CATEGORIES, weights=CATEGORY_W)[0]


def _sample_amount() -> float:
    """
    Amount distribution:
      5 %  high outliers  $200–$450
      7 %  low tail       $8–$22
     88 %  bulk           $20–$200  (lognormal centred ~$48)
    """
    r = random.random()
    if r < 0.05:
        return round(random.uniform(200.0, 450.0), 2)
    if r < 0.12:
        return round(random.uniform(8.0, 22.0), 2)
    return round(float(np.clip(np.random.lognormal(3.70, 0.55), 20.0, 200.0)), 2)


# ─── Three-period surge distribution ─────────────────────────────────────────
#   oldest  (days  0–29)  15 % of chargebacks
#   middle  (days 30–59)  30 %
#   recent  (days 60–89)  55 %  ← heavier in recent weeks

TOTAL = 1_000   # target record count; seed keeps this exact

PERIOD_EDGES = [
    (START,                       START + timedelta(days=29)),
    (START + timedelta(days=30),  START + timedelta(days=59)),
    (START + timedelta(days=60),  TODAY),
]
PERIOD_WEIGHTS = [0.15, 0.30, 0.55]

# Exact counts that sum to TOTAL (no rounding drift)
counts = [int(TOTAL * w) for w in PERIOD_WEIGHTS]
counts[-1] = TOTAL - sum(counts[:-1])

# ─── Build chargeback rows ────────────────────────────────────────────────────
rows = []
for (d0, d1), n in zip(PERIOD_EDGES, counts):
    for _ in range(n):
        # 70 % of chargebacks land on problem merchants (M001–M008)
        merch = (
            random.choice(merchants[:8])
            if random.random() < 0.70
            else random.choice(merchants[8:])
        )
        d   = _rand_date(d0, d1)
        cat = _pick_category(merch["merchant_id"], d)
        pm  = random.choices(PAYMENT_METHODS, weights=PAYMENT_W)[0]
        rows.append({
            "chargeback_id":     str(uuid.uuid4()),
            "chargeback_date":   _iso_ts(d),
            "merchant_id":       merch["merchant_id"],
            "merchant_name":     merch["merchant_name"],
            "merchant_category": merch["merchant_category"],
            "product_name":      random.choice(
                                     PRODUCTS.get(merch["merchant_category"],
                                                  PRODUCTS["electronics"])
                                 ),
            "amount":            _sample_amount(),
            "currency":          "USD",
            "country":           random.choices(COUNTRIES, weights=COUNTRY_W)[0],
            "payment_method":    pm,
            "processor":         random.choice(PROCESSORS[pm]),
            "reason_code":       random.choice(REASON_CODES[cat]),
            "category":          cat,
        })

cb = pd.DataFrame(rows)
cb.to_csv(CHARGEBACKS_OUT, index=False)
print(f"chargebacks.csv      {len(cb):,} rows  →  {CHARGEBACKS_OUT}")

# ─── Diagnostics ─────────────────────────────────────────────────────────────
print("\n  category %   :", dict(
    cb["category"].value_counts(normalize=True).apply(lambda x: f"{x:.0%}")))
print("  country  %   :", dict(
    cb["country"].value_counts(normalize=True).apply(lambda x: f"{x:.0%}")))
print("  payment  %   :", dict(
    cb["payment_method"].value_counts(normalize=True).apply(lambda x: f"{x:.0%}")))
print(f"  unique merchants : {cb['merchant_id'].nunique()}")

_dates = pd.to_datetime(cb["chargeback_date"]).dt.date
_days_ago = _dates.apply(lambda d: (TODAY - d).days)

spike = cb[(cb["merchant_id"] == FRAUD_SPIKE_MID) & (_days_ago <= 10)]
print(f"\n  Fraud spike  (M003, last 10 d)  : {len(spike):3d} rows, "
      f"fraud share {spike['category'].eq('fraud').mean():.0%}")

pnr = cb[cb["merchant_id"] == PNR_STEADY_MID]
print(f"  PNR steady   (M006, all 90 d)   : {len(pnr):3d} rows, "
      f"PNR share {pnr['category'].eq('product_not_received').mean():.0%}")

weekend_mask = _dates.apply(lambda d: d.weekday() >= 5)
wk = cb[weekend_mask]
print(f"  Weekend rows                    : {len(wk):3d}, "
      f"fraud share {wk['category'].eq('fraud').mean():.0%}  "
      f"(vs {cb['category'].eq('fraud').mean():.0%} overall)")

# ─── Generate transactions_daily.csv ─────────────────────────────────────────
# Strategy: derive daily transaction counts from chargeback counts so that
#   implied chargeback rate  ≈  8–14 % for problem merchants
#                            ≈  1.5–3 % for normal merchants
# transactions_amount  = transactions_count × random average order value

rng = np.random.default_rng(SEED)

cb["_date"] = pd.to_datetime(cb["chargeback_date"]).dt.date
grp = (
    cb
    .groupby(["_date", "merchant_id", "country", "payment_method", "processor"])
    .agg(cb_count=("chargeback_id", "count"), cb_amount=("amount", "sum"))
    .reset_index()
)

tx_rows = []
for _, r in grp.iterrows():
    is_problem = r["merchant_id"] in PROBLEM_SET
    rate       = float(rng.uniform(0.08, 0.14) if is_problem
                       else rng.uniform(0.015, 0.030))
    tx_cnt     = max(int(r["cb_count"] / rate), int(r["cb_count"]))
    avg_order  = float(rng.uniform(40.0, 120.0))
    tx_rows.append({
        "date":                str(r["_date"]),
        "merchant_id":         r["merchant_id"],
        "country":             r["country"],
        "payment_method":      r["payment_method"],
        "processor":           r["processor"],
        "transactions_count":  tx_cnt,
        "transactions_amount": round(tx_cnt * avg_order, 2),
    })

tx = pd.DataFrame(tx_rows)
tx.to_csv(TRANSACTIONS_OUT, index=False)
print(f"\ntransactions_daily.csv {len(tx):,} rows  →  {TRANSACTIONS_OUT}")

# Implied chargeback rates summary
cb_by_m = cb.groupby("merchant_id").size().rename("chargebacks")
tx_by_m = tx.groupby("merchant_id")["transactions_count"].sum()
rate_df = pd.concat([cb_by_m, tx_by_m], axis=1).dropna()
rate_df["rate_%"] = (
    rate_df["chargebacks"] / rate_df["transactions_count"] * 100
).round(1)
print("\n  implied chargeback rate – top 10 merchants:")
print(
    rate_df.sort_values("rate_%", ascending=False)
    .head(10)
    .to_string()
)
print("\nDone.")
