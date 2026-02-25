"""
Acceptance tests for /api/metrics and /api/chargebacks.

Proven facts about the seeded dataset (SEED=42, 1 000 chargeback rows):
  Overall chargeback rate      ≈  5.33 %
  Problem merchants M001-M008  ≈ 11 %   (vs ~2.5 % for normal merchants)
  Country rates (approximate)  ID 5.24 %  PH 5.02 %  TH 5.52 %  VN 5.97 %
  Payment method rates         gcash 6.42 %  visa 5.02 %  truemoney 4.93 %
  Last-10-day rate             ≈  5.71 %
  Oldest-7-day rate            ≈  5.94 %

Run from the project root:
    pytest tests/ -q
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
import requests

BASE = "http://localhost:8000"

# ── fixed date anchors (derived from SEED=42 90-day window) ──────────────────
TODAY = date.today()
START = TODAY - timedelta(days=89)           # oldest date in dataset
OLDEST_7_END = START + timedelta(days=6)     # 7-day slice at oldest end
LAST_10_START = TODAY - timedelta(days=9)    # fraud-spike window for M003


# ═══════════════════════════════════════════════════════════════════════════
# 1. HTTP status codes
# ═══════════════════════════════════════════════════════════════════════════

class TestStatusCodes:
    def test_health_200(self):
        r = requests.get(f"{BASE}/api/health")
        assert r.status_code == 200

    def test_metrics_200(self):
        r = requests.get(f"{BASE}/api/metrics")
        assert r.status_code == 200, r.text

    def test_chargebacks_200(self):
        r = requests.get(f"{BASE}/api/chargebacks")
        assert r.status_code == 200, r.text


# ═══════════════════════════════════════════════════════════════════════════
# 2. Response structure / shape
# ═══════════════════════════════════════════════════════════════════════════

class TestResponseStructure:
    def test_metrics_required_keys(self):
        data = requests.get(f"{BASE}/api/metrics").json()
        required = {
            "total_chargebacks", "total_disputed_amount",
            "chargeback_rate", "trend_pct",
            "by_category", "by_country", "by_payment_method",
            "by_day", "top_merchants",
        }
        missing = required - data.keys()
        assert not missing, f"Missing keys in /api/metrics: {missing}"

    def test_metrics_value_types(self):
        data = requests.get(f"{BASE}/api/metrics").json()
        assert isinstance(data["total_chargebacks"], int)
        assert isinstance(data["total_disputed_amount"], float)
        assert isinstance(data["chargeback_rate"], float)
        assert isinstance(data["trend_pct"], float)
        assert isinstance(data["by_category"], list)
        assert isinstance(data["top_merchants"], list)

    def test_chargebacks_required_keys(self):
        data = requests.get(f"{BASE}/api/chargebacks").json()
        for key in ("records", "total", "page", "page_size"):
            assert key in data, f"Missing key '{key}' in /api/chargebacks"

    def test_chargebacks_records_are_list(self):
        data = requests.get(f"{BASE}/api/chargebacks").json()
        assert isinstance(data["records"], list)
        assert len(data["records"]) > 0

    def test_chargebacks_record_columns(self):
        data = requests.get(f"{BASE}/api/chargebacks", params={"page_size": 1}).json()
        rec = data["records"][0]
        for col in ("chargeback_id", "merchant_id", "merchant_name",
                    "country", "reason_category", "payment_method", "amount_usd"):
            assert col in rec, f"Column '{col}' missing from chargeback record"

    def test_top_merchants_shape(self):
        data = requests.get(f"{BASE}/api/metrics").json()
        assert len(data["top_merchants"]) > 0
        m = data["top_merchants"][0]
        for key in ("merchant_id", "merchant_name", "count", "amount", "rate"):
            assert key in m, f"Missing key '{key}' in top_merchants entry"


# ═══════════════════════════════════════════════════════════════════════════
# 3. Filters change outputs (count goes down, remains > 0)
# ═══════════════════════════════════════════════════════════════════════════

class TestFiltersChangeOutputs:
    @pytest.fixture(scope="class")
    def total_all(self):
        return requests.get(f"{BASE}/api/metrics").json()["total_chargebacks"]

    def test_filter_date_range(self, total_all):
        start = (TODAY - timedelta(days=29)).isoformat()
        end   = TODAY.isoformat()
        n = requests.get(f"{BASE}/api/metrics",
                         params={"start_date": start, "end_date": end}
                         ).json()["total_chargebacks"]
        assert 0 < n < total_all, (
            f"Date-range filter should reduce count: {n} vs {total_all}"
        )

    def test_filter_merchant_id(self, total_all):
        n = requests.get(f"{BASE}/api/metrics",
                         params={"merchant_id": "M001"}).json()["total_chargebacks"]
        assert 0 < n < total_all

    def test_filter_reason_category(self, total_all):
        n = requests.get(f"{BASE}/api/metrics",
                         params={"reason_category": "fraud"}).json()["total_chargebacks"]
        assert 0 < n < total_all

    def test_filter_payment_method(self, total_all):
        n = requests.get(f"{BASE}/api/metrics",
                         params={"payment_method": "visa"}).json()["total_chargebacks"]
        assert 0 < n < total_all

    def test_filter_country(self, total_all):
        n = requests.get(f"{BASE}/api/metrics",
                         params={"country": "ID"}).json()["total_chargebacks"]
        assert 0 < n < total_all

    def test_filter_amount_range(self, total_all):
        n = requests.get(f"{BASE}/api/metrics",
                         params={"min_amount": 50, "max_amount": 150}
                         ).json()["total_chargebacks"]
        assert 0 < n < total_all

    def test_combined_filters_further_reduce_count(self, total_all):
        single = requests.get(f"{BASE}/api/metrics",
                               params={"country": "ID"}).json()["total_chargebacks"]
        combo  = requests.get(f"{BASE}/api/metrics",
                               params={"country": "ID",
                                       "payment_method": "visa"}
                               ).json()["total_chargebacks"]
        assert 0 < combo <= single, (
            "Adding a second filter should not increase count"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 4. Chargeback-rate changes correctly with filters
#    Numerator = filtered chargebacks; denominator = matching transactions slice
# ═══════════════════════════════════════════════════════════════════════════

class TestChargebackRate:
    @pytest.fixture(scope="class")
    def rate_all(self):
        return requests.get(f"{BASE}/api/metrics").json()["chargeback_rate"]

    def test_overall_rate_not_zero(self, rate_all):
        assert rate_all > 0

    def test_overall_rate_not_hardcoded_legacy(self, rate_all):
        """Old code always returned 1/37 * 100 = 2.70 % regardless of filters."""
        legacy = round(100 / 37, 2)   # 2.70
        assert rate_all != legacy, (
            f"Rate appears to still be hardcoded: {rate_all}% == {legacy}%"
        )

    def test_rate_in_valid_range(self, rate_all):
        assert 0 < rate_all < 100

    # ── merchant_id filter ────────────────────────────────────────────────

    def test_rate_changes_with_problem_merchant_filter(self, rate_all):
        """Problem merchant (M001 ~11%) should have a higher rate than overall (~5.3%)."""
        rate_m001 = requests.get(f"{BASE}/api/metrics",
                                  params={"merchant_id": "M001"}
                                  ).json()["chargeback_rate"]
        assert rate_m001 != rate_all, (
            f"Problem merchant rate ({rate_m001}%) should differ from overall ({rate_all}%)"
        )
        assert rate_m001 > rate_all, (
            f"Problem merchant (M001) rate {rate_m001}% should exceed overall {rate_all}%"
        )

    def test_rate_changes_with_normal_merchant_filter(self, rate_all):
        """Normal merchant (M034 ~2.6%) should have a lower rate than overall (~5.3%)."""
        rate_m034 = requests.get(f"{BASE}/api/metrics",
                                  params={"merchant_id": "M034"}
                                  ).json()["chargeback_rate"]
        assert rate_m034 != rate_all, (
            f"Normal merchant rate ({rate_m034}%) should differ from overall ({rate_all}%)"
        )
        assert rate_m034 < rate_all, (
            f"Normal merchant (M034) rate {rate_m034}% should be below overall {rate_all}%"
        )

    def test_problem_merchant_rate_exceeds_normal_merchant_rate(self):
        """Structural invariant: problem merchants always have higher rates than normal ones."""
        r_problem = requests.get(f"{BASE}/api/metrics",
                                  params={"merchant_id": "M002"}).json()["chargeback_rate"]
        r_normal  = requests.get(f"{BASE}/api/metrics",
                                  params={"merchant_id": "M020"}).json()["chargeback_rate"]
        assert r_problem > r_normal, (
            f"Problem M002 ({r_problem}%) should exceed normal M020 ({r_normal}%)"
        )

    # ── country filter ────────────────────────────────────────────────────

    def test_rate_changes_with_country_filter(self, rate_all):
        """ID rate (~5.24%) and VN rate (~5.97%) both differ from overall (~5.33%)."""
        rate_id = requests.get(f"{BASE}/api/metrics",
                                params={"country": "ID"}).json()["chargeback_rate"]
        rate_vn = requests.get(f"{BASE}/api/metrics",
                                params={"country": "VN"}).json()["chargeback_rate"]
        assert rate_id != rate_all, (
            f"country=ID rate ({rate_id}%) should differ from unfiltered ({rate_all}%)"
        )
        assert rate_vn != rate_all, (
            f"country=VN rate ({rate_vn}%) should differ from unfiltered ({rate_all}%)"
        )
        # VN should have a higher rate than ID in this dataset
        assert rate_vn > rate_id, (
            f"VN rate ({rate_vn}%) should exceed ID rate ({rate_id}%)"
        )

    # ── date range filter ─────────────────────────────────────────────────

    def test_rate_changes_with_narrow_date_window(self, rate_all):
        """
        Oldest 7-day window has a different merchant mix → different implied rate.
        Expected ~5.94 % vs overall ~5.33 %.
        """
        rate_7d = requests.get(
            f"{BASE}/api/metrics",
            params={
                "start_date": START.isoformat(),
                "end_date":   OLDEST_7_END.isoformat(),
            },
        ).json()["chargeback_rate"]
        assert rate_7d != rate_all, (
            f"Narrow date window rate ({rate_7d}%) should differ from 90-day rate ({rate_all}%)"
        )

    def test_rate_changes_with_last_10_days(self, rate_all):
        """
        Last-10-day window includes M003 fraud spike → elevated rate.
        Expected ~5.71 % vs overall ~5.33 %.
        """
        rate_10d = requests.get(
            f"{BASE}/api/metrics",
            params={
                "start_date": LAST_10_START.isoformat(),
                "end_date":   TODAY.isoformat(),
            },
        ).json()["chargeback_rate"]
        assert rate_10d != rate_all, (
            f"Last-10-day rate ({rate_10d}%) should differ from 90-day rate ({rate_all}%)"
        )

    # ── per-merchant rates in top_merchants ───────────────────────────────

    def test_top_merchants_rates_vary(self):
        """
        Top-merchants list should show heterogeneous rates
        (not all identical), proving per-merchant rate is wired up.
        """
        merchants = requests.get(f"{BASE}/api/metrics").json()["top_merchants"]
        rates = [m["rate"] for m in merchants]
        assert len(set(rates)) > 1, (
            f"All top-merchant rates are identical ({rates[0]}%); "
            "per-merchant rate computation is not varying."
        )

    def test_top_merchants_problem_rates_above_normal(self):
        """
        Among the top 10 merchants, the first 8 slots should be dominated
        by problem merchants (M001-M008) and their rates should be above 8%.
        """
        merchants = requests.get(f"{BASE}/api/metrics").json()["top_merchants"]
        problem_rates = [m["rate"] for m in merchants
                         if m["merchant_id"] in {f"M{i:03d}" for i in range(1, 9)}]
        assert problem_rates, "No problem merchants in top-10"
        assert all(r > 8 for r in problem_rates), (
            f"Problem merchant rates should all exceed 8%, got {problem_rates}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 5. /api/chargebacks – pagination and sorting
# ═══════════════════════════════════════════════════════════════════════════

class TestChargebacksPaginationSorting:
    def test_pagination_returns_correct_page_meta(self):
        r1 = requests.get(f"{BASE}/api/chargebacks",
                           params={"page": 1, "page_size": 10}).json()
        r2 = requests.get(f"{BASE}/api/chargebacks",
                           params={"page": 2, "page_size": 10}).json()
        assert r1["page"] == 1
        assert r2["page"] == 2
        assert len(r1["records"]) == 10
        assert len(r2["records"]) == 10

    def test_pages_have_non_overlapping_records(self):
        r1 = requests.get(f"{BASE}/api/chargebacks",
                           params={"page": 1, "page_size": 20}).json()
        r2 = requests.get(f"{BASE}/api/chargebacks",
                           params={"page": 2, "page_size": 20}).json()
        ids1 = {rec["chargeback_id"] for rec in r1["records"]}
        ids2 = {rec["chargeback_id"] for rec in r2["records"]}
        assert ids1.isdisjoint(ids2), "Page 1 and page 2 share records"

    def test_total_is_consistent_across_pages(self):
        r1 = requests.get(f"{BASE}/api/chargebacks",
                           params={"page": 1, "page_size": 50}).json()
        r2 = requests.get(f"{BASE}/api/chargebacks",
                           params={"page": 2, "page_size": 50}).json()
        assert r1["total"] == r2["total"], (
            f"Total differs across pages: {r1['total']} vs {r2['total']}"
        )

    def test_sort_date_ascending(self):
        data = requests.get(f"{BASE}/api/chargebacks",
                             params={"sort_by": "date", "sort_dir": "asc",
                                     "page_size": 20}).json()
        dates = [rec["date"] for rec in data["records"]]
        assert dates == sorted(dates), f"Dates are not ascending: {dates[:5]}"

    def test_sort_date_descending(self):
        data = requests.get(f"{BASE}/api/chargebacks",
                             params={"sort_by": "date", "sort_dir": "desc",
                                     "page_size": 20}).json()
        dates = [rec["date"] for rec in data["records"]]
        assert dates == sorted(dates, reverse=True), (
            f"Dates are not descending: {dates[:5]}"
        )

    def test_sort_asc_desc_first_records_differ(self):
        asc  = requests.get(f"{BASE}/api/chargebacks",
                             params={"sort_by": "date", "sort_dir": "asc",
                                     "page_size": 1}).json()
        desc = requests.get(f"{BASE}/api/chargebacks",
                             params={"sort_by": "date", "sort_dir": "desc",
                                     "page_size": 1}).json()
        assert asc["records"][0]["chargeback_id"] != desc["records"][0]["chargeback_id"], (
            "First record with asc and desc sort should be different"
        )

    def test_sort_by_amount_descending(self):
        data = requests.get(f"{BASE}/api/chargebacks",
                             params={"sort_by": "amount_usd", "sort_dir": "desc",
                                     "page_size": 10}).json()
        amounts = [rec["amount_usd"] for rec in data["records"]]
        assert amounts == sorted(amounts, reverse=True), (
            f"Amounts not descending: {amounts}"
        )

    def test_sort_by_processor(self):
        """Sorting by processor should not raise an error (regression: status was broken)."""
        r = requests.get(f"{BASE}/api/chargebacks",
                          params={"sort_by": "processor", "sort_dir": "asc",
                                  "page_size": 5})
        assert r.status_code == 200

    def test_last_page_is_partial(self):
        """The last page should have fewer records than page_size."""
        total = requests.get(f"{BASE}/api/chargebacks").json()["total"]
        page_size = 50
        last_page = (total // page_size) + 1
        data = requests.get(f"{BASE}/api/chargebacks",
                             params={"page": last_page, "page_size": page_size}).json()
        expected_size = total % page_size or page_size
        assert len(data["records"]) == expected_size, (
            f"Last page: expected {expected_size} records, got {len(data['records'])}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 6. Filter consistency between /api/metrics and /api/chargebacks
# ═══════════════════════════════════════════════════════════════════════════

class TestFilterConsistency:
    @pytest.mark.parametrize("params", [
        {"country": "ID"},
        {"payment_method": "visa"},
        {"reason_category": "fraud"},
        {"merchant_id": "M003"},
        {"country": "PH", "payment_method": "gopay"},
    ])
    def test_metrics_and_chargebacks_agree_on_count(self, params):
        metrics = requests.get(f"{BASE}/api/metrics", params=params).json()
        cb_resp = requests.get(f"{BASE}/api/chargebacks",
                                params={**params, "page_size": 1}).json()
        assert metrics["total_chargebacks"] == cb_resp["total"], (
            f"Count mismatch for {params}: "
            f"metrics={metrics['total_chargebacks']}, chargebacks={cb_resp['total']}"
        )

    def test_empty_filter_returns_all(self):
        metrics = requests.get(f"{BASE}/api/metrics").json()
        cb_resp = requests.get(f"{BASE}/api/chargebacks",
                                params={"page_size": 1}).json()
        assert metrics["total_chargebacks"] == cb_resp["total"]

    def test_impossibly_narrow_amount_returns_zero(self):
        metrics = requests.get(f"{BASE}/api/metrics",
                                params={"min_amount": 999, "max_amount": 1000}
                                ).json()
        assert metrics["total_chargebacks"] == 0
        assert metrics["chargeback_rate"] == 0.0
