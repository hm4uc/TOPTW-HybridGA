"""
Thí nghiệm 2: Đánh giá Giá trị Cá nhân hóa (Personalization Value).

★ CHIẾN LƯỢC ★
  • Chạy trên C101 (Narrow TW — consistent with exp1/exp3/exp4)
  • Budget nới rộng (2_000_000) → isolate preference from financial constraints
  • 5 profiles: baseline, history_buff, foodie, explorer, shopper
  • 10 runs per profile

Usage:
    cd backend
    py -m experiments.exp2_personalization
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from experiments.benchmark_runner import run_batch, INSTANCE_CONFIGS
from app.models.requests import UserPreferences

# ══════════════════════════════════════════════════════════════════════════════
#  Cấu hình
# ══════════════════════════════════════════════════════════════════════════════
INSTANCE = "C101"
NUM_RUNS = 10
OUTPUT_DIR = "experiments/results/exp2_personalization"

# 5 user profiles khác nhau
USER_PROFILES = {
    "baseline": {
        "history_culture": 3, "nature_parks": 3,
        "food_drink": 3, "shopping": 3, "entertainment": 3,
    },
    "history_buff": {
        "history_culture": 5, "nature_parks": 2,
        "food_drink": 3, "shopping": 1, "entertainment": 1,
    },
    "foodie": {
        "history_culture": 1, "nature_parks": 2,
        "food_drink": 5, "shopping": 1, "entertainment": 3,
    },
    "explorer": {
        "history_culture": 3, "nature_parks": 5,
        "food_drink": 2, "shopping": 1, "entertainment": 4,
    },
    "shopper": {
        "history_culture": 1, "nature_parks": 1,
        "food_drink": 3, "shopping": 5, "entertainment": 2,
    },
}

# Budget nới rộng → isolate preference effect
BUDGET = 2_000_000


def main():
    cfg = INSTANCE_CONFIGS[INSTANCE]

    print("=" * 70)
    print("  THÍ NGHIỆM 2: ĐÁNH GIÁ GIÁ TRỊ CÁ NHÂN HÓA")
    print(f"  Instance: {INSTANCE} | Budget: {BUDGET:,}")
    print(f"  Profiles: {len(USER_PROFILES)} | Runs/profile: {NUM_RUNS}")
    print("=" * 70)

    all_results = {}

    for profile_name, interests in USER_PROFILES.items():
        print(f"\n{'#' * 70}")
        print(f"  PROFILE: {profile_name}")
        print(f"  Interests: {interests}")
        print(f"{'#' * 70}")

        prefs = UserPreferences(
            budget=BUDGET,
            start_time=0.0,
            end_time=cfg["depot_due"] / 60.0,  # Solomon time → giờ
            start_node_id=0,
            interests=interests,
        )
        df = run_batch(
            instance_name=INSTANCE,
            user_prefs=prefs,
            num_runs=NUM_RUNS,
            output_dir=OUTPUT_DIR,
            label=profile_name,
        )
        all_results[profile_name] = df

    # ── Bảng tổng hợp ───────────────────────────────────────────────────────
    cat_cols = ["cat_history_culture", "cat_nature_parks", "cat_food_drink",
                "cat_shopping", "cat_entertainment"]
    cat_short = ["Hist", "Nat", "Food", "Shop", "Ent"]

    print(f"\n\n{'=' * 110}")
    print("  BẢNG TỔNG HỢP — PHÂN BỐ CATEGORY THEO PROFILE (Số lượng + Tỷ lệ %)")
    print(f"{'=' * 110}")

    # Header
    header_parts = [f"{'Profile':<15}", f"{'Score':>8}", f"{'±Std':>6}",
                    f"{'POIs':>5}", f"{'Cost':>10}"]
    for s in cat_short:
        header_parts.append(f"{'│':>2}")
        header_parts.append(f"{s:>5}")
        header_parts.append(f"{'(%)':>5}")
    print("".join(header_parts))
    print("─" * 110)

    for name, df in all_results.items():
        score = df['total_score'].mean()
        std = df['total_score'].std()
        pois = df['num_pois'].mean()
        cost = df['total_cost'].mean()

        cats = {}
        for col in cat_cols:
            cats[col] = df[col].mean() if col in df.columns else 0

        total_pois = sum(cats.values())

        # Build row
        row_parts = [f"{name:<15}", f"{score:8.1f}", f"{std:6.1f}",
                     f"{pois:5.1f}", f"{cost:10.0f}"]
        for col in cat_cols:
            v = cats[col]
            pct = (v / total_pois * 100) if total_pois > 0 else 0
            row_parts.append(f"{'│':>2}")
            row_parts.append(f"{v:5.1f}")
            row_parts.append(f"{pct:4.0f}%")
        print("".join(row_parts))

    print(f"\n  ★ Instance: {INSTANCE} — Budget: {BUDGET:,}")
    print(f"  ★ Tỷ lệ % = (Số POI danh mục / Tổng POI trong route) × 100")


if __name__ == "__main__":
    main()
