"""
Analyze Results — Tổng hợp kết quả từ CSV + Xuất bảng so sánh.

Đọc tất cả CSV từ các thí nghiệm đã chạy,
tạo bảng tổng hợp chuẩn khoa học + xuất ra CSV summary.

Usage:
    cd backend
    py -m experiments.analyze_results
"""

import os
import sys
import glob
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

RESULTS_DIR = "experiments/results"
SUMMARY_DIR = os.path.join(RESULTS_DIR, "summary")
os.makedirs(SUMMARY_DIR, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
#  BKS + GVNS từ Labadie et al. (2012) — m=1 route
# ══════════════════════════════════════════════════════════════════════════════
LABADIE_BKS = {
    "C101": 320, "C201": 870, "R101": 198,
    "R201": 797, "RC101": 219, "RC201": 795,
}

LABADIE_GVNS = {
    "C101":  {"min": 320,  "avg": 320.0,  "max": 320,  "gap": 0.0, "time": 0.2},
    "C201":  {"min": 850,  "avg": 850.0,  "max": 850,  "gap": 2.3, "time": 0.1},
    "R101":  {"min": 197,  "avg": 197.0,  "max": 197,  "gap": 0.5, "time": 0.2},
    "R201":  {"min": 765,  "avg": 775.6,  "max": 785,  "gap": 2.7, "time": 6.7},
    "RC101": {"min": 219,  "avg": 219.0,  "max": 219,  "gap": 0.0, "time": 2.1},
    "RC201": {"min": 778,  "avg": 784.0,  "max": 788,  "gap": 1.4, "time": 3.7},
}

INSTANCES = ["C101", "C201", "R101", "R201", "RC101", "RC201"]


def analyze_exp1_benchmark():
    """TN1: Bảng so sánh HGA vs GVNS — chuẩn khoa học."""
    print("\n" + "=" * 120)
    print("  THÍ NGHIỆM 1: SO SÁNH HGA vs LABADIE GVNS (2012) — m=1 route")
    print("=" * 120)

    rows = []
    for inst in INSTANCES:
        csv_path = os.path.join(RESULTS_DIR, "exp1_benchmark", f"{inst}_fixed.csv")
        if not os.path.exists(csv_path):
            print(f"  ⚠ Missing: {csv_path}")
            continue

        df = pd.read_csv(csv_path)
        bks = LABADIE_BKS[inst]
        gvns = LABADIE_GVNS[inst]

        hga_best = df['total_score'].max()
        hga_worst = df['total_score'].min()
        hga_avg = df['total_score'].mean()
        hga_std = df['total_score'].std()
        hga_time = df['execution_time'].mean()
        hga_pois = df['num_pois'].mean()
        hga_gap = (bks - hga_avg) / bks * 100
        num_runs = len(df)

        rows.append({
            "Instance": inst,
            "BKS": bks,
            "GVNS_Best": gvns["min"],
            "GVNS_Avg": gvns["avg"],
            "GVNS_Max": gvns["max"],
            "GVNS_Gap%": gvns["gap"],
            "GVNS_Time(s)": gvns["time"],
            "HGA_Best": hga_best,
            "HGA_Avg": round(hga_avg, 1),
            "HGA_Worst": hga_worst,
            "HGA_Std": round(hga_std, 1),
            "HGA_Gap%": round(hga_gap, 1),
            "HGA_Time(s)": round(hga_time, 3),
            "HGA_POIs": round(hga_pois, 1),
            "Runs": num_runs,
        })

    summary_df = pd.DataFrame(rows)

    # Print formatted table
    print(f"\n{'Instance':<10} {'BKS':>5} │ {'GVNS':>5} {'GVNS':>7} {'GVNS':>6} │ {'HGA':>6} {'HGA':>7} {'HGA':>6} {'HGA':>6} │ {'':>5}")
    print(f"{'':10} {'':>5} │ {'Best':>5} {'Avg':>7} {'Gap%':>6} │ {'Best':>6} {'Avg':>7} {'Std':>6} {'Gap%':>6} │ {'T(s)':>5}")
    print("─" * 85)

    for r in rows:
        print(f"{r['Instance']:<10} {r['BKS']:>5} │ "
              f"{r['GVNS_Best']:>5} {r['GVNS_Avg']:>7.1f} {r['GVNS_Gap%']:>5.1f}% │ "
              f"{r['HGA_Best']:>6.0f} {r['HGA_Avg']:>7.1f} {r['HGA_Std']:>6.1f} {r['HGA_Gap%']:>5.1f}% │ "
              f"{r['HGA_Time(s)']:>5.3f}")

    # Save CSV
    out_path = os.path.join(SUMMARY_DIR, "exp1_benchmark_summary.csv")
    summary_df.to_csv(out_path, index=False)
    print(f"\n  📄 Summary saved to: {out_path}")
    return summary_df


def analyze_exp2_personalization():
    """TN2: Bảng so sánh profiles trên C201 (Wide TW)."""
    print("\n" + "=" * 100)
    print("  THÍ NGHIỆM 2: GIÁ TRỊ CÁ NHÂN HÓA (C201 — Wide TW)")
    print("=" * 100)

    profiles = ["baseline", "history_buff", "foodie", "explorer", "shopper"]
    cat_cols = ["cat_history_culture", "cat_nature_parks", "cat_food_drink",
                "cat_shopping", "cat_entertainment"]
    cat_short = ["Hist", "Nat", "Food", "Shop", "Ent"]

    rows = []
    for name in profiles:
        # Ưu tiên C201, fallback C101 nếu chưa chạy lại
        csv_path = os.path.join(RESULTS_DIR, "exp2_personalization", f"C201_{name}.csv")
        if not os.path.exists(csv_path):
            csv_path = os.path.join(RESULTS_DIR, "exp2_personalization", f"C101_{name}.csv")
        if not os.path.exists(csv_path):
            continue
        df = pd.read_csv(csv_path)

        cat_vals = {}
        for col in cat_cols:
            cat_vals[col] = df[col].mean() if col in df.columns else 0
        total_pois_cat = sum(cat_vals.values())

        row = {
            "Profile": name,
            "Score_Avg": round(df['total_score'].mean(), 1),
            "Score_Std": round(df['total_score'].std(), 1),
            "POIs_Avg": round(df['num_pois'].mean(), 1),
            "Cost_Avg": round(df['total_cost'].mean(), 0),
        }
        for col, short in zip(cat_cols, cat_short):
            v = cat_vals[col]
            pct = (v / total_pois_cat * 100) if total_pois_cat > 0 else 0
            row[short] = round(v, 1)
            row[f"{short}%"] = round(pct, 1)
        rows.append(row)

    summary_df = pd.DataFrame(rows)

    # Print table with % 
    print(f"\n{'Profile':<15} {'Score':>7} {'±Std':>6} {'POIs':>5} {'Cost':>10} │ "
          f"{'Hist':>5} {'%':>4} {'Nat':>5} {'%':>4} {'Food':>5} {'%':>4} "
          f"{'Shop':>5} {'%':>4} {'Ent':>5} {'%':>4}")
    print("─" * 110)
    for r in rows:
        print(f"{r['Profile']:<15} {r['Score_Avg']:>7.1f} {r['Score_Std']:>6.1f} "
              f"{r['POIs_Avg']:>5.1f} {r['Cost_Avg']:>10.0f} │ "
              f"{r['Hist']:>5.1f} {r['Hist%']:>3.0f}% "
              f"{r['Nat']:>5.1f} {r['Nat%']:>3.0f}% "
              f"{r['Food']:>5.1f} {r['Food%']:>3.0f}% "
              f"{r['Shop']:>5.1f} {r['Shop%']:>3.0f}% "
              f"{r['Ent']:>5.1f} {r['Ent%']:>3.0f}%")

    out_path = os.path.join(SUMMARY_DIR, "exp2_personalization_summary.csv")
    summary_df.to_csv(out_path, index=False)
    print(f"\n  📄 Summary saved to: {out_path}")
    return summary_df


def analyze_exp3_ablation():
    """TN3: Ablation Study — đóng góp từng thành phần."""
    print("\n" + "=" * 100)
    print("  THÍ NGHIỆM 3: ABLATION STUDY")
    print("=" * 100)

    variants = ["full_hga", "no_smart_repair", "no_insertion_mut",
                "no_wait_penalty", "no_heuristic_init", "no_diversity_check"]

    rows = []
    baseline_score = None

    for name in variants:
        csv_path = os.path.join(RESULTS_DIR, "exp3_ablation", f"C101_{name}.csv")
        if not os.path.exists(csv_path):
            continue
        df = pd.read_csv(csv_path)

        avg_score = df['total_score'].mean()
        if name == "full_hga":
            baseline_score = avg_score

        row = {
            "Variant": name,
            "Score_Best": df['total_score'].max(),
            "Score_Avg": round(avg_score, 1),
            "Score_Worst": df['total_score'].min(),
            "Score_Std": round(df['total_score'].std(), 1),
            "Wait_Avg": round(df['total_wait'].mean(), 1),
            "Gens_Avg": round(df['generations_run'].mean(), 1),
            "Time(s)": round(df['execution_time'].mean(), 3),
            "Diff%": 0.0,
        }
        rows.append(row)

    # Calculate diff from baseline
    for r in rows:
        if baseline_score and baseline_score > 0:
            r["Diff%"] = round((r["Score_Avg"] - baseline_score) / baseline_score * 100, 2)

    summary_df = pd.DataFrame(rows)

    print(f"\n{'Variant':<22} {'Best':>7} {'Avg':>7} {'Worst':>7} {'±Std':>6} "
          f"{'Wait':>7} {'Gens':>5} {'Diff%':>7}")
    print("─" * 80)
    for r in rows:
        diff_str = "baseline" if r["Variant"] == "full_hga" else f"{r['Diff%']:>+6.1f}%"
        print(f"{r['Variant']:<22} {r['Score_Best']:>7.0f} {r['Score_Avg']:>7.1f} "
              f"{r['Score_Worst']:>7.0f} {r['Score_Std']:>6.1f} "
              f"{r['Wait_Avg']:>7.1f} {r['Gens_Avg']:>5.0f} {diff_str:>8}")

    out_path = os.path.join(SUMMARY_DIR, "exp3_ablation_summary.csv")
    summary_df.to_csv(out_path, index=False)
    print(f"\n  📄 Summary saved to: {out_path}")
    return summary_df


def analyze_exp4_sensitivity():
    """TN4: Sensitivity Analysis — Normalized Score (% of BKS) trên 6 instances."""
    print("\n" + "=" * 110)
    print("  THÍ NGHIỆM 4: SENSITIVITY ANALYSIS — Normalized Score (% of BKS) trên 6 Instances")
    print("=" * 110)

    instances = ["C101", "C201", "R101", "R201", "RC101", "RC201"]
    bks = {"C101": 320, "C201": 870, "R101": 198,
           "R201": 797, "RC101": 219, "RC201": 795}

    param_grid = {
        "population_size": [50, 100, 150, 200],
        "mutation_rate": [0.3, 0.5, 0.7, 0.9],
        "tournament_k": [2, 3, 5, 7],
        "stagnation_limit": [15, 25, 40, 60],
    }
    defaults = {"population_size": 100, "mutation_rate": 0.7,
                "tournament_k": 3, "stagnation_limit": 25}

    all_rows = []
    for param, values in param_grid.items():
        print(f"\n  ── {param} (default = {defaults[param]}) ──")
        print(f"  {'Value':>10} {'Norm%':>8} {'±Std':>7} {'T(s)':>8} {'Gens':>6}  "
              f"{'C101':>6} {'C201':>6} {'R101':>6} {'R201':>6} {'RC101':>6} {'RC201':>6}")
        print(f"  {'-' * 95}")

        for val in values:
            norm_scores = []
            per_inst = {}
            total_time = 0
            total_gens = 0
            inst_count = 0

            for inst in instances:
                csv_path = os.path.join(
                    RESULTS_DIR, "exp4_sensitivity", f"{inst}_{param}_{val}.csv"
                )
                if not os.path.exists(csv_path):
                    per_inst[inst] = None
                    continue
                df = pd.read_csv(csv_path)
                inst_norm = (df['total_score'] / bks[inst] * 100).tolist()
                norm_scores.extend(inst_norm)
                per_inst[inst] = sum(inst_norm) / len(inst_norm)
                total_time += df['execution_time'].mean()
                total_gens += df['generations_run'].mean()
                inst_count += 1

            if not norm_scores:
                continue

            avg_norm = sum(norm_scores) / len(norm_scores)
            std_norm = pd.Series(norm_scores).std()
            avg_time = total_time / max(inst_count, 1)
            avg_gens = total_gens / max(inst_count, 1)

            marker = " ◄" if val == defaults[param] else ""

            row = {
                "Parameter": param,
                "Value": val,
                "Norm_Score%": round(avg_norm, 2),
                "Norm_Std": round(std_norm, 2),
                "Time(s)": round(avg_time, 3),
                "Gens_Avg": round(avg_gens, 1),
            }
            for inst in instances:
                row[f"Norm_{inst}"] = round(per_inst[inst], 1) if per_inst[inst] is not None else None
            all_rows.append(row)

            # Per-instance string
            per_str = "  ".join(
                f"{per_inst[inst]:6.1f}" if per_inst[inst] is not None else "   N/A"
                for inst in instances
            )
            print(f"  {val:>10} {avg_norm:8.2f} {std_norm:7.2f} "
                  f"{avg_time:8.3f} {avg_gens:6.1f}{marker}  {per_str}")

    summary_df = pd.DataFrame(all_rows)
    out_path = os.path.join(SUMMARY_DIR, "exp4_sensitivity_summary.csv")
    summary_df.to_csv(out_path, index=False)
    print(f"\n  📄 Summary saved to: {out_path}")

    # Tìm best config cho mỗi param
    print(f"\n  ── BEST CONFIG ──")
    for param in param_grid:
        param_rows = [r for r in all_rows if r["Parameter"] == param]
        if param_rows:
            best = max(param_rows, key=lambda r: r["Norm_Score%"])
            print(f"  {param}: best value = {best['Value']} "
                  f"(Norm = {best['Norm_Score%']:.2f}%, Time = {best['Time(s)']:.3f}s)")

    return summary_df


def main():
    print("╔" + "═" * 78 + "╗")
    print("║  PHÂN TÍCH KẾT QUẢ THỰC NGHIỆM HGA-TOPTW  —  BẢNG TỔNG HỢP CHUẨN KHOA HỌC  ║")
    print("╚" + "═" * 78 + "╝")

    analyze_exp1_benchmark()
    analyze_exp2_personalization()
    analyze_exp3_ablation()
    analyze_exp4_sensitivity()

    print(f"\n\n{'=' * 80}")
    print(f"  ✅ TẤT CẢ BẢNG TỔNG HỢP ĐÃ ĐƯỢC LƯU VÀO: {SUMMARY_DIR}")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()

