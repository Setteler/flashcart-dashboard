"""
One-shot data generation script for FlashCart chargeback data.
Run this to produce chargebacks.csv (900+ records).
"""
import uuid
import random
import numpy as np
import pandas as pd
from datetime import date, timedelta

random.seed(42)
np.random.seed(42)

# --- Date setup ---
today = date.today()
start_date = today - timedelta(days=89)  # 90 days inclusive

# Date ranges
oldest_end = start_date + timedelta(days=29)
middle_start = start_date + timedelta(days=30)
middle_end = start_date + timedelta(days=59)
recent_start = start_date + timedelta(days=60)

def random_date_in_range(d_start: date, d_end: date) -> date:
    delta = (d_end - d_start).days
    return d_start + timedelta(days=random.randint(0, delta))

# --- Distributions ---
COUNTRIES = ["ID", "PH", "TH", "VN"]
COUNTRY_WEIGHTS = [0.40, 0.25, 0.20, 0.15]

REASON_CATEGORIES = [
    "fraud",
    "product_not_received",
    "product_not_as_described",
    "duplicate_processing",
    "subscription_cancelled",
]
REASON_WEIGHTS = [0.40, 0.30, 0.15, 0.08, 0.07]

REASON_CODE_MAP = {
    "fraud": ["10.4", "10.5", "10.2"],
    "product_not_received": ["13.1"],
    "product_not_as_described": ["13.3"],
    "duplicate_processing": ["12.6"],
    "subscription_cancelled": ["13.2"],
}

PAYMENT_METHODS = ["visa", "mastercard", "gopay", "ovo", "gcash", "truemoney", "bank_transfer"]
PAYMENT_WEIGHTS = [0.35, 0.25, 0.12, 0.10, 0.08, 0.05, 0.05]

MERCHANT_CATEGORIES = ["electronics", "accessories", "gaming", "mobile_phones"]

MERCHANT_NAMES = [
    "TechZone PH", "GadgetHub ID", "GamersParadise", "MobileKing TH",
    "AccessoryWorld", "ElectroShop VN", "QuickGadgets", "PhoneMax ID",
    "DigiStore", "GamingGear PH", "TechMart VN", "CoolPhone TH",
    "AccessPro", "ElectraBuy", "SmartGadgets", "MobileHub",
    "GearUp PH", "TechPulse ID", "GameStop VN", "PhoneZone TH",
    "AccessHub", "ElectroMall", "SmartStore", "MobilePro VN",
    "GadgetPro TH", "TechGo ID", "GameWorld", "PhoneMart PH",
    "AccessZone", "ElectroGo", "SmartHub VN", "MobileZone ID",
    "GadgetStore TH", "TechHub PH", "GameZone", "PhoneHub VN",
    "AccessMart", "ElectroZone ID", "SmartMart TH", "MobileStore PH",
    "GadgetMall VN", "TechStore", "GameHub ID", "PhoneStore TH",
    "AccessStore PH", "ElectroHub VN", "SmartZone", "MobileGear ID",
    "GadgetZone PH", "TechMall TH", "GameMart VN", "PhonePro ID",
    "AccessGear", "ElectroStore PH", "SmartGear VN", "MobileMall TH",
    "GadgetGear ID", "TechPro VN", "GameStore PH", "PhoneGear TH",
]

# Build merchant list: M001-M008 are problem merchants, rest are normal
merchants = []
for i in range(1, 61):
    mid = f"M{i:03d}"
    name = MERCHANT_NAMES[i - 1]
    cat = random.choice(MERCHANT_CATEGORIES)
    merchants.append({"merchant_id": mid, "merchant_name": name, "merchant_category": cat})

# --- Record generation ---
TOTAL_RECORDS = 910  # aim for 900+

# Period record counts (surge distribution)
oldest_count = int(TOTAL_RECORDS * 0.15)   # ~137
middle_count = int(TOTAL_RECORDS * 0.30)   # ~273
recent_count = TOTAL_RECORDS - oldest_count - middle_count  # ~500

records = []

def make_records(n: int, d_start: date, d_end: date):
    for _ in range(n):
        reason_cat = random.choices(REASON_CATEGORIES, weights=REASON_WEIGHTS)[0]
        reason_code = random.choice(REASON_CODE_MAP[reason_cat])
        payment = random.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS)[0]
        country = random.choices(COUNTRIES, weights=COUNTRY_WEIGHTS)[0]

        # Pick merchant: problem merchants (M001-M008) get higher probability
        # We'll assign during post-processing; here just pick randomly weighted
        roll = random.random()
        if roll < 0.72:  # 72% of records go to problem merchants M001-M008
            merch = merchants[random.randint(0, 7)]
        else:
            merch = merchants[random.randint(8, 59)]

        amount = float(np.clip(np.random.lognormal(mean=3.5, sigma=0.9), 8, 450))
        amount = round(amount, 2)

        status = random.choices(["open", "won", "lost"], weights=[0.45, 0.25, 0.30])[0]

        records.append({
            "chargeback_id": str(uuid.uuid4()),
            "date": random_date_in_range(d_start, d_end).isoformat(),
            "merchant_id": merch["merchant_id"],
            "merchant_name": merch["merchant_name"],
            "merchant_category": merch["merchant_category"],
            "country": country,
            "reason_category": reason_cat,
            "reason_code": reason_code,
            "payment_method": payment,
            "amount_usd": amount,
            "status": status,
        })

make_records(oldest_count, start_date, oldest_end)
make_records(middle_count, middle_start, middle_end)
make_records(recent_count, recent_start, today)

df = pd.DataFrame(records)
output_path = "chargebacks.csv"
df.to_csv(output_path, index=False)
print(f"Generated {len(df)} records → {output_path}")
print(df["reason_category"].value_counts())
print(df["country"].value_counts())
print(df["payment_method"].value_counts())
print("\nTop merchants by chargeback count:")
print(df.groupby("merchant_id").size().sort_values(ascending=False).head(10))
