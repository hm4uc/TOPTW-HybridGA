"""
Thí nghiệm 4: Phân tích Độ nhạy (Sensitivity Analysis).

★ CHIẾN LƯỢC ★
  • Chạy trên TOÀN BỘ 6 instances (C101, C201, R101, R201, RC101, RC201)
  • Mỗi instance chuẩn hóa score bằng BKS → Normalized Score (0-100%)
  • Lấy trung bình chuẩn hóa → kết quả robust, không bị thiên lệch

Usage:
    cd backend
    py -m experiments.exp4_sensitivity
"""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from experiments.benchmark_runner import run_batch, create_fixed_prefs, INSTANCE_CONFIGS

# ══════════════════════════════════════════════════════════════════════════════
#  Cấu hình
# ══════════════════════════════════════════════════════════════════════════════
INSTANCES = ["C101", "C201", "R101", "R201", "RC101", "RC201"]
NUM_RUNS = 5   # 5 runs × 6 instances × 16 configs = 480 runs tổng
OUTPUT_DIR = "experiments/results/exp4_sensitivity"

# BKS để chuẩn hóa score (từ Labadie 2012)
BKS = {
    "C101": 320, "C201": 870, "R101": 198,
    "R201": 797, "RC101": 219, "RC201": 795,
}

# ══════════════════════════════════════════════════════════════════════════════
#  Parameter Grid
# ══════════════════════════════════════════════════════════════════════════════
PARAM_GRID = {
    "population_size": [50, 100, 150, 200],
    "mutation_rate": [0.3, 0.5, 0.7, 0.9],
    "tournament_k": [2, 3, 5, 7],
    "stagnation_limit": [15, 25, 40, 60],
}

# Giá trị mặc định
DEFAULTS = {
    "population_size": 100,
    "mutation_rate": 0.7,
    "tournament_k": 3,
    "stagnation_limit": 25,
}


def main():
    print("=" * 70)
    print("  THÍ NGHIỆM 4: SENSITIVITY ANALYSIS (6 Instances, Normalized)")
    print(f"  Instances: {INSTANCES}")
    print(f"  Runs/config/instance: {NUM_RUNS}")
    total_runs = NUM_RUNS * len(INSTANCES) * sum(len(v) for v in PARAM_GRID.values())
    print(f"  Tổng số runs: {total_runs}")
    print("=" * 70)

    # Dict lưu: {label: {instance: df, ...}}
    all_results = {}

    for param_name, values in PARAM_GRID.items():
        print(f"\n{'#' * 70}")
        print(f"  PARAMETER: {param_name}")
        print(f"  Values: {values} (default: {DEFAULTS[param_name]})")
        print(f"{'#' * 70}")

        for val in values:
            ga_params = {param_name: val}
            label = f"{param_name}_{val}"
            all_results[label] = {"param": param_name, "value": val, "dfs": {}}

            for inst in INSTANCES:
                print(f"\n  --- {param_name}={val} on {inst} ---")
                prefs = create_fixed_prefs(inst)

                df = run_batch(
                    instance_name=inst,
                    user_prefs=prefs,
                    num_runs=NUM_RUNS,
                    output_dir=OUTPUT_DIR,
                    label=label,
                    ga_params=ga_params,
                    # Tắt wait penalty để so sánh công bằng với BKS
                    ablation_flags={"use_wait_penalty": False},
                )
                all_results[label]["dfs"][inst] = df

    # ══════════════════════════════════════════════════════════════════════════
    #  Bảng tổng hợp — Normalized Score (% of BKS)
    # ══════════════════════════════════════════════════════════════════════════
    print(f"\n\n{'=' * 90}")
    print("  BẢNG TỔNG HỢP — SENSITIVITY ANALYSIS (Normalized % of BKS)")
    print(f"{'=' * 90}")

    summary_rows = []

    for param_name, values in PARAM_GRID.items():
        print(f"\n  ── {param_name} (default = {DEFAULTS[param_name]}) ──")
        print(f"  {'Value':>10} {'Norm Score%':>12} {'±Std':>8} "
              f"{'Time(s)':>10} {'Gens':>8}  Per-Instance Norm%")
        print(f"  {'-' * 80}")

        for val in values:
            label = f"{param_name}_{val}"
            if label not in all_results:
                continue

            dfs = all_results[label]["dfs"]
            norm_scores = []
            per_inst = {}

            for inst, df in dfs.items():
                bks = BKS[inst]
                inst_norm = df['total_score'].mean() / bks * 100
                norm_scores.extend((df['total_score'] / bks * 100).tolist())
                per_inst[inst] = inst_norm

            avg_norm = sum(norm_scores) / len(norm_scores)
            std_norm = pd.Series(norm_scores).std()
            avg_time = sum(df['execution_time'].mean() for df in dfs.values()) / len(dfs)
            avg_gens = sum(df['generations_run'].mean() for df in dfs.values()) / len(dfs)

            marker = " ◄" if val == DEFAULTS[param_name] else ""
            per_str = " | ".join(f"{inst[:4]}={per_inst[inst]:.1f}" for inst in INSTANCES)

            print(f"  {val:>10} {avg_norm:12.2f}% {std_norm:8.2f} "
                  f"{avg_time:10.3f} {avg_gens:8.1f}{marker}  [{per_str}]")

            summary_rows.append({
                "Param": param_name,
                "Value": val,
                "Norm_Score%": round(avg_norm, 2),
                "Norm_Std": round(std_norm, 2),
                "Time(s)": round(avg_time, 3),
                "Gens": round(avg_gens, 1),
                **{f"Norm_{inst}": round(per_inst[inst], 2) for inst in INSTANCES},
            })

    # Lưu CSV summary
    summary_df = pd.DataFrame(summary_rows)
    os.makedirs("experiments/results/summary", exist_ok=True)
    out_path = "experiments/results/summary/exp4_sensitivity_normalized.csv"
    summary_df.to_csv(out_path, index=False)
    print(f"\n  📄 Normalized summary saved to: {out_path}")


if __name__ == "__main__":
    main()
