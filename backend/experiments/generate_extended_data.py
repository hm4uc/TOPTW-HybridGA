"""
Generate Extended CSV — Thêm CATEGORY + PRICE cố định vào Solomon instances.

Chạy 1 lần duy nhất. Output là 6 file CSV cố định.
Mọi thí nghiệm sau đều đọc từ file này → đảm bảo Reproducibility.

Seed = CUST_NO (POI ID) → cùng 1 POI luôn có cùng category + price.

Usage:
    cd backend
    python -m experiments.generate_extended_data
"""

import csv
import os
import random

# ── Category Configuration ───────────────────────────────────────────────────
CATEGORIES = [
    'history_culture',   # Lăng Bác, Văn Miếu, Hoàng Thành, ...
    'nature_parks',      # Công viên Thống Nhất, Hồ Gươm, ...
    'food_drink',        # Phở Thìn, Bún Chả, Cà phê Giảng, ...
    'shopping',          # Chợ Đồng Xuân, Vincom, ...
    'entertainment',     # Nhà hát Lớn, Rạp chiếu phim, ...
]

# Tỷ lệ phân bố giả lập (đặc thù du lịch Hà Nội)
CATEGORY_WEIGHTS = [0.35, 0.15, 0.25, 0.15, 0.10]

# ── Bảng giá theo loại hình (VND) ────────────────────────────────────────────
CATEGORY_PRICE_TIERS: dict[str, list[float]] = {
    'nature_parks':    [0.0],
    'history_culture': [30_000.0, 50_000.0, 100_000.0],
    'entertainment':   [100_000.0, 200_000.0, 500_000.0],
    'food_drink':      [50_000.0, 150_000.0, 300_000.0, 800_000.0],
    'shopping':        [0.0, 100_000.0, 300_000.0, 500_000.0],
}

INSTANCES = ["C101", "C201", "R101", "R201", "RC101", "RC201"]


def generate_extended(instance_name: str, base_dir: str) -> None:
    """Đọc Solomon CSV gốc, thêm CATEGORY + PRICE, lưu file extended."""
    input_path = os.path.join(base_dir, 'data', 'solomon_instances', f'{instance_name}.csv')
    output_dir = os.path.join(base_dir, 'data', 'solomon_instances', 'extended')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'{instance_name}_extended.csv')

    rows = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cust_no = int(row['CUST NO.'])
            pid = cust_no - 1  # Remap: 1-based → 0-based (CUST 1 = Depot id=0)

            if pid == 0:
                cat = "depot"
                price = 0.0
            else:
                # Seed cố định theo POI ID → luôn reproducible
                rng = random.Random(pid)
                cat = rng.choices(CATEGORIES, weights=CATEGORY_WEIGHTS, k=1)[0]
                price = rng.choice(CATEGORY_PRICE_TIERS[cat])

            row['CATEGORY'] = cat
            row['PRICE'] = price
            rows.append(row)

    # Ghi ra CSV mới
    fieldnames = list(rows[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Log category distribution
    cats = [r['CATEGORY'] for r in rows if r['CATEGORY'] != 'depot']
    dist = {c: cats.count(c) for c in CATEGORIES}
    print(f"  ✅ {instance_name}_extended.csv — {len(rows)} nodes")
    print(f"     Category distribution: {dist}")


def main():
    """Generate extended CSV cho tất cả 6 instances."""
    # Tìm thư mục backend (chạy từ backend/)
    base_dir = os.getcwd()
    if not os.path.exists(os.path.join(base_dir, 'data', 'solomon_instances')):
        # Thử lên 1 cấp
        base_dir = os.path.dirname(base_dir)

    print("=" * 60)
    print("  GENERATE EXTENDED CSV — Reproducible Category + Price")
    print("=" * 60)

    for inst in INSTANCES:
        generate_extended(inst, base_dir)

    print(f"\n{'=' * 60}")
    print(f"  ✅ TẤT CẢ {len(INSTANCES)} EXTENDED CSV ĐÃ ĐƯỢC TẠO.")
    output_dir = os.path.join(base_dir, 'data', 'solomon_instances', 'extended')
    print(f"  📁 Thư mục: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
