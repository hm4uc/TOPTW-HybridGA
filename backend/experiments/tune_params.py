"""
Cross-Instance Parameter Tuning.

Test các tham số trên CẢ 6 instances để tìm bộ tham số tối ưu TỔNG THỂ.
Mỗi config: 5 runs × 6 instances = 30 runs.

Usage:
    cd backend
    py -m experiments.tune_params
"""

import os
import sys
import time
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from experiments.benchmark_runner import run_single, create_fixed_prefs

INSTANCES = ["C101", "C201", "R101", "R201", "RC101", "RC201"]
LABADIE_BKS = {
    "C101": 320, "C201": 870, "R101": 198,
    "R201": 797, "RC101": 219, "RC201": 795,
}

NUM_RUNS = 5
OUTPUT_DIR = "experiments/results/tuning"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_config(config_name: str, ga_params: dict) -> dict:
    """Test 1 cấu hình trên tất cả 6 instances, trả về avg gap% tổng thể."""
    print(f"\n{'='*70}")
    print(f"  CONFIG: {config_name} | params = {ga_params}")
    print(f"{'='*70}")

    instance_gaps = {}
    instance_scores = {}

    for inst in INSTANCES:
        prefs = create_fixed_prefs(inst)
        bks = LABADIE_BKS[inst]
        scores = []

        for run in range(NUM_RUNS):
            result = run_single(inst, prefs, ga_params=ga_params)
            scores.append(result['total_score'])

        avg_score = sum(scores) / len(scores)
        best_score = max(scores)
        gap = (bks - avg_score) / bks * 100

        instance_gaps[inst] = gap
        instance_scores[inst] = {
            "best": best_score, "avg": round(avg_score, 1),
            "gap": round(gap, 1)
        }
        print(f"    {inst}: Best={best_score:.0f}, Avg={avg_score:.1f}, Gap={gap:.1f}%")

    avg_gap = sum(instance_gaps.values()) / len(instance_gaps)
    print(f"  >>> AVG GAP across all instances: {avg_gap:.1f}%")

    return {
        "config": config_name,
        "params": ga_params,
        "avg_gap": round(avg_gap, 1),
        "instance_scores": instance_scores,
        "instance_gaps": instance_gaps,
    }


def main():
    print("╔" + "═" * 68 + "╗")
    print("║  CROSS-INSTANCE PARAMETER TUNING — Tìm tham số tối ưu tổng thể  ║")
    print("╚" + "═" * 68 + "╝")
    print(f"  Instances: {INSTANCES}")
    print(f"  Runs per config per instance: {NUM_RUNS}")
    print(f"  Total runs per config: {NUM_RUNS * len(INSTANCES)}")

    start = time.perf_counter()

    # ── Cấu hình test ────────────────────────────────────────────────────
    configs = [
        # Baseline (current defaults)
        ("baseline_pop50_mr0.5_k5_stag15",
         {"population_size": 50, "mutation_rate": 0.5, "tournament_k": 5, "stagnation_limit": 15}),

        # Tăng stagnation (giúp wide TW instances)
        ("stag25_pop50_mr0.5_k5",
         {"population_size": 50, "mutation_rate": 0.5, "tournament_k": 5, "stagnation_limit": 25}),
        ("stag40_pop50_mr0.5_k5",
         {"population_size": 50, "mutation_rate": 0.5, "tournament_k": 5, "stagnation_limit": 40}),

        # Tăng population (giúp diversity)
        ("pop100_mr0.5_k5_stag25",
         {"population_size": 100, "mutation_rate": 0.5, "tournament_k": 5, "stagnation_limit": 25}),

        # Mutation rate cao hơn
        ("pop100_mr0.7_k5_stag25",
         {"population_size": 100, "mutation_rate": 0.7, "tournament_k": 5, "stagnation_limit": 25}),

        # Tournament k thấp hơn (giữ diversity)
        ("pop100_mr0.5_k3_stag25",
         {"population_size": 100, "mutation_rate": 0.5, "tournament_k": 3, "stagnation_limit": 25}),

        # Combo tối ưu dự đoán
        ("pop100_mr0.5_k3_stag40",
         {"population_size": 100, "mutation_rate": 0.5, "tournament_k": 3, "stagnation_limit": 40}),

        # K thấp + mutation cao + stag cao
        ("pop100_mr0.7_k3_stag40",
         {"population_size": 100, "mutation_rate": 0.7, "tournament_k": 3, "stagnation_limit": 40}),
    ]

    results = []
    for config_name, ga_params in configs:
        result = test_config(config_name, ga_params)
        results.append(result)

    # ── Bảng tổng hợp ───────────────────────────────────────────────────
    print(f"\n\n{'='*100}")
    print("  BẢNG TỔNG HỢP — CROSS-INSTANCE TUNING")
    print(f"{'='*100}")
    print(f"  {'Config':<40} {'Avg Gap%':>8} |", end="")
    for inst in INSTANCES:
        print(f" {inst:>6}", end="")
    print()
    print("  " + "-" * 90)

    # Sort by avg_gap
    results.sort(key=lambda r: r["avg_gap"])

    rows = []
    for r in results:
        print(f"  {r['config']:<40} {r['avg_gap']:>7.1f}% |", end="")
        row = {"Config": r["config"], "Avg_Gap%": r["avg_gap"]}
        for inst in INSTANCES:
            gap = r["instance_gaps"].get(inst, 99)
            print(f" {gap:>5.1f}%", end="")
            row[f"{inst}_Gap%"] = gap
        row["Params"] = str(r["params"])
        rows.append(row)
        print()

    best = results[0]
    print(f"\n  🏆 BEST CONFIG: {best['config']}")
    print(f"     Avg Gap: {best['avg_gap']}%")
    print(f"     Params: {best['params']}")

    # Save CSV
    df = pd.DataFrame(rows)
    out_path = os.path.join(OUTPUT_DIR, "tuning_results.csv")
    df.to_csv(out_path, index=False)
    print(f"\n  📄 Results saved to: {out_path}")

    elapsed = time.perf_counter() - start
    print(f"\n  ⏱️ Total time: {elapsed:.1f}s ({elapsed/60:.1f} min)")


if __name__ == "__main__":
    main()
