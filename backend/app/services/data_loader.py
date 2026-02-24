import os
import csv
import copy
import random
from typing import Optional, List
from app.models.domain import POI

# --- DANH SÁCH CATEGORY CHUẨN ---
# Dùng bộ này cho toàn bộ hệ thống
CATEGORIES = [
    'history_culture',  # Lăng Bác, Văn Miếu, Hoàng Thành, Chùa Một Cột, ...
    'nature_parks',     # Công viên Thống Nhất, Hồ Gươm, Vườn hoa Lý Thái Tổ, ...
    'food_drink',       # Phở Thìn, Bún Chả Hương Liên, Cà phê Giảng, ...
    'shopping',         # Chợ Đồng Xuân, Vincom Bà Triệu, Tràng Tiền Plaza, ...
    'entertainment'     # Rạp chiếu phim Quốc gia, Nhà hát Lớn Hà Nội, ...
]

# Tỷ lệ xuất hiện giả lập (Mô phỏng đặc thù du lịch Hà Nội)
# history_culture: 35%, nature: 15%, food: 25%, shopping: 15%, entertainment: 10%
CATEGORY_WEIGHTS = [0.35, 0.15, 0.25, 0.15, 0.10]

# ── BẢNG GIÁ THEO LOẠI HÌNH (Pricing Tiers) ────────────────────────────────
# Mỗi category có mảng giá riêng, phản ánh đặc thù du lịch Hà Nội.
# Khi gán giá, hệ thống random.choice() từ mảng tương ứng (seed = PID).
#
# ┌──────────────────┬──────────────────────────────────┬───────────────────────────────────┐
# │  Category        │  Mức giá (VND)                   │  Giải thích                       │
# ├──────────────────┼──────────────────────────────────┼───────────────────────────────────┤
# │  nature_parks    │  [0]                             │  Luôn miễn phí (Hồ Gươm, đi dạo) │
# │  history_culture │  [30k, 50k, 100k]               │  Vé Nhà nước, giá niêm yết rẻ     │
# │  entertainment   │  [100k, 200k, 500k]             │  Vé tư nhân (show, khu vui chơi)  │
# │  food_drink      │  [50k, 150k, 300k, 800k]        │  Vỉa hè → Bình dân → Cafe → Fine │
# │  shopping        │  [0, 100k, 300k, 500k]          │  0 = Window Shop, còn lại = spend │
# └──────────────────┴──────────────────────────────────┴───────────────────────────────────┘
CATEGORY_PRICE_TIERS: dict[str, list[float]] = {
    'nature_parks':    [0.0],
    'history_culture': [30_000.0, 50_000.0, 100_000.0],
    'entertainment':   [100_000.0, 200_000.0, 500_000.0],
    'food_drink':      [50_000.0, 150_000.0, 300_000.0, 800_000.0],
    'shopping':        [0.0, 100_000.0, 300_000.0, 500_000.0],
}


# =============================================================================
#  IN-MEMORY CACHE  (Singleton Pattern)
# =============================================================================
#
#  Đọc file CSV từ disk đúng 1 lần duy nhất → lưu vào RAM.
#  Các request sau chỉ lấy deep copy từ bộ nhớ, tránh disk I/O lặp lại.
#
#  Tại sao deep copy mà không phải shallow copy?
#    → GA engine MUTATE các object POI trong quá trình chạy (route manipulation).
#    → Nếu dùng shallow copy, nhiều request đồng thời sẽ chia sẻ cùng
#      object POI → race condition, data corruption.
#    → Deep copy đảm bảo mỗi request có bản sao riêng, an toàn hoàn toàn.
#
# =============================================================================

_POI_CACHE: Optional[List[POI]] = None


def _load_from_disk() -> List[POI]:
    """
    Internal: Đọc file C101.csv từ disk và parse thành list[POI].
    Chỉ được gọi 1 lần duy nhất bởi load_solomon_c101().
    """
    file_path = os.path.join(os.getcwd(), 'data', 'solomon_instances', 'C101.csv')

    pois = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cust_no = int(row.get('CUST NO.', 0))

                # --- Remap: CUST NO. 1 → Depot (id=0), others → id = CUST NO. - 1 ---
                pid = cust_no - 1

                # --- LOGIC GÁN CATEGORY + PRICE ---
                if pid == 0:
                    cat = "depot"
                    price = 0.0
                else:
                    # Gán category + price cố định theo PID (seed đảm bảo tái lập)
                    rng = random.Random(pid)
                    cat = rng.choices(CATEGORIES, weights=CATEGORY_WEIGHTS, k=1)[0]

                    # Gán giá vé theo category tier
                    price = rng.choice(CATEGORY_PRICE_TIERS[cat])

                poi = POI(
                    id=pid,
                    x=float(row.get('XCOORD.', 0)),
                    y=float(row.get('YCOORD.', 0)),
                    score=float(row.get('DEMAND', 0)),
                    open_time=float(row.get('READY TIME', 0)),
                    close_time=float(row.get('DUE DATE', 0)),
                    duration=float(row.get('SERVICE TIME', 0)),
                    category=cat,
                    price=price
                )
                pois.append(poi)
    except Exception as e:
        print(f"[DataLoader] Error reading Solomon data: {e}")
        return []

    print(f"[DataLoader] Loaded {len(pois)} POIs from C101.csv "
          f"(Depot id=0 at ({pois[0].x}, {pois[0].y}))")
    return pois


def load_solomon_c101() -> list[POI]:
    """
    Load Solomon C101 benchmark dataset — CÓ CACHE.

    Lần gọi đầu tiên: đọc từ disk → lưu vào _POI_CACHE.
    Các lần gọi sau : trả deep copy từ RAM (không đọc disk).

    Returns a list of POI objects. POI with id=0 is always the Depot.
    """
    global _POI_CACHE

    if _POI_CACHE is None:
        _POI_CACHE = _load_from_disk()
        print(f"[DataLoader] Cache initialized: {len(_POI_CACHE)} POIs in RAM")
    else:
        print(f"[DataLoader] Cache HIT — returning {len(_POI_CACHE)} POIs from RAM")

    # Deep copy để mỗi request có bản sao riêng, tránh race condition
    return copy.deepcopy(_POI_CACHE)