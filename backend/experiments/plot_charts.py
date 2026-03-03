"""
Visualization — Vẽ đồ thị cho báo cáo khóa luận.

Tạo:
  1. Convergence Curve: Best/Avg Fitness vs Generation
  2. Ablation Boxplot: So sánh Total Score giữa các variant
  3. Route Scatter Plot: So sánh lộ trình Foodie vs History Buff
  4. Personalization Bar Chart: Category distribution theo profile
  5. Sensitivity Line Chart: Score vs Parameter value

Usage:
    cd backend
    py -m experiments.plot_charts
"""

import os
import sys
import json
import glob
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

# ── Cấu hình font tiếng Việt-safe ──────────────────────────────────────────
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
matplotlib.rcParams['figure.dpi'] = 150

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

CHART_DIR = "experiments/results/charts"
os.makedirs(CHART_DIR, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
#  1. Convergence Curve
# ══════════════════════════════════════════════════════════════════════════════
def plot_convergence(csv_path: str, output_name: str = "convergence"):
    """
    Vẽ Convergence Curve từ convergence_log trong CSV.
    Lấy run đầu tiên làm đại diện.
    Hiển thị: Best, Median, Avg Fitness.
    """
    df = pd.read_csv(csv_path)
    if 'convergence_log' not in df.columns:
        print(f"  ⚠ Không tìm thấy convergence_log trong {csv_path}")
        return

    # Lấy convergence log từ run đầu tiên
    log = json.loads(df.iloc[0]['convergence_log'])
    gens = [r["gen"] for r in log]
    best = [r["best_fitness"] for r in log]
    avg = [r["avg_fitness"] for r in log]
    # median_fitness có thể chưa tồn tại trong data cũ
    median = [r.get("median_fitness", r["avg_fitness"]) for r in log]

    instance = df.iloc[0].get('instance', 'Unknown')
    label = df.iloc[0].get('label', '')

    plt.figure(figsize=(10, 6))
    plt.plot(gens, best, 'b-', label='Best Fitness', linewidth=2)
    plt.plot(gens, median, 'g-.', label='Median Fitness', linewidth=1.5, alpha=0.8)
    plt.plot(gens, avg, 'r--', label='Avg Fitness', alpha=0.6, linewidth=1.2)
    plt.fill_between(gens, avg, best, alpha=0.08, color='blue')
    plt.xlabel('Generation', fontsize=12)
    plt.ylabel('Fitness', fontsize=12)
    plt.title(f'Convergence Curve — {instance} [{label}]', fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    path = os.path.join(CHART_DIR, f"{output_name}.png")
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✅ {path}")


# ══════════════════════════════════════════════════════════════════════════════
#  2. Ablation Boxplot
# ══════════════════════════════════════════════════════════════════════════════
def plot_ablation_boxplot(results_dir: str = "experiments/results/exp3_ablation"):
    """Boxplot so sánh Normalized Score (% of BKS) giữa các variant ablation (6 instances)."""
    bks = {"C101": 320, "C201": 870, "R101": 198,
           "R201": 797, "RC101": 219, "RC201": 795}

    csv_files = sorted(glob.glob(os.path.join(results_dir, "*.csv")))
    if not csv_files:
        print(f"  ⚠ Không tìm thấy CSV trong {results_dir}")
        return

    dfs = []
    for f in csv_files:
        df = pd.read_csv(f)
        dfs.append(df)
    all_data = pd.concat(dfs, ignore_index=True)

    # Extract variant name from label (e.g., "full_hga_C101" → "full_hga")
    variants = ["full_hga", "no_smart_repair", "no_insertion_mut",
                "no_wait_penalty", "no_heuristic_init", "no_diversity_check"]

    # Compute normalized score for each row
    all_data['variant'] = all_data['label'].apply(
        lambda lbl: next((v for v in variants if lbl.startswith(v)), lbl)
    )
    all_data['instance'] = all_data['label'].apply(
        lambda lbl: lbl.split('_')[-1] if lbl.split('_')[-1] in bks else
                    '_'.join(lbl.split('_')[-2:]) if '_'.join(lbl.split('_')[-2:]) in bks else 'Unknown'
    )
    all_data['norm_score'] = all_data.apply(
        lambda row: row['total_score'] / bks.get(row['instance'], 1) * 100
        if row['instance'] in bks else row['total_score'], axis=1
    )

    existing_order = [v for v in variants if v in all_data['variant'].unique()]
    if not existing_order:
        # Fallback: old format (single instance, label = variant name)
        existing_order = [v for v in variants if v in all_data['label'].unique()]
        all_data['variant'] = all_data['label']
        all_data['norm_score'] = all_data['total_score']

    plot_data = [all_data[all_data['variant'] == v]['norm_score'].values for v in existing_order]

    fig, ax = plt.subplots(figsize=(12, 7))
    bp = ax.boxplot(plot_data, patch_artist=True, labels=existing_order)

    colors = ['#4CAF50', '#FF9800', '#2196F3', '#9C27B0', '#F44336', '#795548']
    for patch, color in zip(bp['boxes'], colors[:len(existing_order)]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_xlabel('Variant', fontsize=12)
    ax.set_ylabel('Normalized Score (% of BKS)', fontsize=12)
    ax.set_title('Ablation Study — Component Contribution (6 Instances)', fontsize=14)
    ax.set_xticklabels(existing_order, rotation=20, ha='right')
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()

    path = os.path.join(CHART_DIR, "ablation_boxplot.png")
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✅ {path}")


# ══════════════════════════════════════════════════════════════════════════════
#  3. Route Scatter Plot
# ══════════════════════════════════════════════════════════════════════════════
def plot_route_comparison(results_dir: str = "experiments/results/exp2_personalization"):
    """Vẽ 2 route cạnh nhau: Foodie vs History Buff."""
    from app.services.data_loader import load_solomon_instance

    # Ưu tiên C101, fallback C201
    instance = "C101"
    pois = load_solomon_instance(instance)
    poi_map = {p.id: p for p in pois}

    # Đọc route_ids từ CSV (lấy run 1 = best representative)
    profiles = {}
    for profile_name in ["foodie", "history_buff"]:
        csv_path = os.path.join(results_dir, f"{instance}_{profile_name}.csv")
        if not os.path.exists(csv_path):
            csv_path = os.path.join(results_dir, f"C201_{profile_name}.csv")
        if not os.path.exists(csv_path):
            print(f"  ⚠ Không tìm thấy {csv_path}")
            return
        df = pd.read_csv(csv_path)
        # Lấy run có score cao nhất
        best_row = df.loc[df['total_score'].idxmax()]
        route_ids = json.loads(best_row['route_ids'])
        # Đảm bảo điểm 0 (Depot) luôn có mặt ở đầu và cuối để vẽ không bị lỗi
        route = [poi_map[0]] + [poi_map[pid] for pid in route_ids if pid in poi_map and pid != 0] + [poi_map[0]]
        profiles[profile_name] = route

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    configs = [
        (axes[0], profiles["foodie"], "Foodie", 'tomato'),
        (axes[1], profiles["history_buff"], "History Buff", 'steelblue'),
    ]

    for ax, route, title, color in configs:
        # Vẽ tất cả POI (xám nhạt)
        all_x = [p.x for p in pois if p.id != 0]
        all_y = [p.y for p in pois if p.id != 0]
        ax.scatter(all_x, all_y, c='lightgray', s=30, zorder=1,
                   label='Not visited', alpha=0.6)

        # Vẽ route (màu đậm + nối đường)
        rx = [p.x for p in route]
        ry = [p.y for p in route]
        ax.plot(rx, ry, '-', color=color, linewidth=1.5, alpha=0.6, zorder=2)
        ax.scatter(rx[1:-1], ry[1:-1], c=color, s=80, zorder=3,
                   label=f'Visited ({len(route)-2} POIs)', edgecolors='white')

        # Depot
        depot = route[0]
        ax.scatter([depot.x], [depot.y], c='gold', s=200, marker='*',
                   zorder=4, label='Depot', edgecolors='black')

        ax.set_title(f'{title}', fontsize=14, fontweight='bold')
        ax.set_xlabel('X coordinate')
        ax.set_ylabel('Y coordinate')
        ax.legend(fontsize=9, loc='upper right')
        ax.grid(True, alpha=0.2)

    plt.suptitle(f'Route Comparison ({instance}): Personalization creates different routes',
                 fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()

    path = os.path.join(CHART_DIR, "route_comparison.png")
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✅ {path}")


# ══════════════════════════════════════════════════════════════════════════════
#  4. Personalization Bar Chart
# ══════════════════════════════════════════════════════════════════════════════
def plot_personalization_bars(results_dir: str = "experiments/results/exp2_personalization"):
    """Stacked Bar Chart: Category % distribution theo profile."""
    profiles = ["baseline", "history_buff", "foodie", "explorer", "shopper"]
    cats = ["cat_history_culture", "cat_nature_parks", "cat_food_drink",
            "cat_shopping", "cat_entertainment"]
    cat_labels = ["History", "Nature", "Food", "Shopping", "Entertain"]
    colors = ['#4169E1', '#228B22', '#FF6347', '#DAA520', '#9370DB']

    data = {}
    pois_count = {}
    for name in profiles:
        csv_path = os.path.join(results_dir, f"C101_{name}.csv")
        if not os.path.exists(csv_path):
            csv_path = os.path.join(results_dir, f"C201_{name}.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            vals = [df[c].mean() if c in df.columns else 0 for c in cats]
            total = sum(vals)
            pois_count[name] = total
            # Convert to percentages
            data[name] = [(v / total * 100) if total > 0 else 0 for v in vals]

    if not data:
        print("  ⚠ Không tìm thấy dữ liệu personalization")
        return

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))

    # ── Left: Stacked Percentage Bar Chart ──────────────────────────────────
    ax1 = axes[0]
    x = range(len(data))
    profile_names = list(data.keys())
    bottom = [0] * len(profile_names)

    for cat_idx, cat_label in enumerate(cat_labels):
        vals = [data[name][cat_idx] for name in profile_names]
        bars = ax1.bar(x, vals, bottom=bottom, label=cat_label,
                       color=colors[cat_idx], alpha=0.85, width=0.6)

        # Add % labels inside bars (chỉ khi > 8%)
        for i, (v, b) in enumerate(zip(vals, bottom)):
            if v > 8:
                ax1.text(i, b + v / 2, f'{v:.0f}%', ha='center', va='center',
                         fontsize=9, fontweight='bold', color='white')

        bottom = [b + v for b, v in zip(bottom, vals)]

    ax1.set_xlabel('User Profile', fontsize=12)
    ax1.set_ylabel('Category Distribution (%)', fontsize=12)
    ax1.set_title('Category Distribution by Profile (%)', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(profile_names, rotation=20, ha='right')
    ax1.legend(fontsize=9, loc='upper right')
    ax1.set_ylim(0, 105)
    ax1.grid(True, alpha=0.2, axis='y')

    # ── Right: Grouped Bar (absolute count) ─────────────────────────────────
    ax2 = axes[1]
    width = 0.15
    for i, (name, pcts) in enumerate(data.items()):
        total = pois_count[name]
        abs_vals = [pct / 100 * total for pct in pcts]
        offset = (i - len(data) / 2 + 0.5) * width
        ax2.bar([xi + offset for xi in range(len(cat_labels))], abs_vals, width,
                label=name, alpha=0.85)

    ax2.set_xlabel('Category', fontsize=12)
    ax2.set_ylabel('Average Number of POIs', fontsize=12)
    ax2.set_title('Absolute POI Count by Category', fontsize=14, fontweight='bold')
    ax2.set_xticks(range(len(cat_labels)))
    ax2.set_xticklabels(cat_labels)
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    path = os.path.join(CHART_DIR, "personalization_bars.png")
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✅ {path}")


# ══════════════════════════════════════════════════════════════════════════════
#  5. Sensitivity Line Charts
# ══════════════════════════════════════════════════════════════════════════════
def plot_sensitivity(results_dir: str = "experiments/results/exp4_sensitivity"):
    """Line charts: Normalized Score vs Execution Time Trade-off."""
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

    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    axes = axes.flatten()

    for idx, (param, values) in enumerate(param_grid.items()):
        ax1 = axes[idx]
        ax2 = ax1.twinx()  # Tạo trục Y thứ 2 bên phải

        means_score, stds_score, means_time = [], [], []

        for val in values:
            norm_scores = []
            times = []
            for inst in instances:
                csv_path = os.path.join(results_dir, f"{inst}_{param}_{val}.csv")
                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                    inst_norm = df['total_score'] / bks[inst] * 100
                    norm_scores.extend(inst_norm.tolist())
                    times.extend(df['execution_time'].tolist())

            if norm_scores:
                means_score.append(sum(norm_scores) / len(norm_scores))
                stds_score.append(pd.Series(norm_scores).std())
                means_time.append(sum(times) / len(times))
            else:
                means_score.append(0)
                stds_score.append(0)
                means_time.append(0)

        # Vẽ đường Điểm số (Score) - Trục trái (Màu xanh)
        l1 = ax1.errorbar(values, means_score, yerr=stds_score, marker='o', capsize=5,
                          linewidth=2, markersize=8, color='steelblue', label='Normalized Score')

        # Vẽ đường Thời gian (Time) - Trục phải (Màu cam gạch ngang)
        l2, = ax2.plot(values, means_time, marker='s', linestyle='--', 
                       linewidth=2, markersize=7, color='darkorange', label='Execution Time')

        # Đánh dấu Default
        if defaults[param] in values:
            di = values.index(defaults[param])
            ax1.scatter([defaults[param]], [means_score[di]], color='red',
                        s=180, zorder=5, marker='D', label=f'Default ({defaults[param]})')

        # Formatting
        ax1.set_xlabel(param.replace('_', ' ').title(), fontsize=12)
        ax1.set_ylabel('Normalized Score (% of BKS)', fontsize=12, color='steelblue')
        ax2.set_ylabel('Execution Time (seconds)', fontsize=12, color='darkorange')
        
        ax1.tick_params(axis='y', labelcolor='steelblue')
        ax2.tick_params(axis='y', labelcolor='darkorange')
        
        ax1.set_title(f'Trade-off: {param}', fontsize=13, fontweight='bold')
        ax1.grid(True, alpha=0.3)

        # Gộp legend của cả 2 trục
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc='lower right' if param != 'stagnation_limit' else 'lower right', fontsize=9)

    plt.suptitle('Sensitivity Analysis — Trade-off Between Score and Execution Time',
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()

    path = os.path.join(CHART_DIR, "sensitivity_analysis.png")
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✅ {path}")


# ══════════════════════════════════════════════════════════════════════════════
#  Main — Vẽ tất cả
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("  VẼ ĐỒ THỊ CHO BÁO CÁO")
    print("=" * 60)

    # 1. Convergence Curves
    print("\n[1] Convergence Curves...")
    exp1_dir = "experiments/results/exp1_benchmark"
    if os.path.exists(exp1_dir):
        for f in sorted(glob.glob(os.path.join(exp1_dir, "*.csv"))):
            inst = os.path.basename(f).replace("_fixed.csv", "")
            plot_convergence(f, f"convergence_{inst}")

    # 2. Ablation Boxplot
    print("\n[2] Ablation Boxplot...")
    plot_ablation_boxplot()

    # 3. Route Comparison
    print("\n[3] Route Comparison (Foodie vs History Buff)...")
    plot_route_comparison()

    # 4. Personalization Bars
    print("\n[4] Personalization Category Distribution...")
    plot_personalization_bars()

    # 5. Sensitivity Analysis
    print("\n[5] Sensitivity Analysis...")
    plot_sensitivity()

    print(f"\n{'=' * 60}")
    print(f"  ✅ TẤT CẢ ĐỒ THỊ ĐÃ ĐƯỢC LƯU VÀO: {CHART_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
