import os
import csv
import random
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

# --- GIÁ VÉ GIẢ LẬP ---
# Category miễn phí (không cần mua vé)
FREE_CATEGORIES = {'nature_parks', 'shopping'}
# Bảng giá cho các category có phí
PRICE_OPTIONS = [30_000.0, 50_000.0, 100_000.0]


def load_solomon_c101() -> list[POI]:
    """
    Load Solomon C101 benchmark dataset from CSV file.
    Returns a list of POI objects. POI with id=0 is always the Depot.
    
    Note: CUST NO. starts from 1 in the CSV file. We treat the FIRST row (CUST NO. = 1)
    as the Depot (id = 0). All subsequent customers are id = CUST_NO - 1... 
    Actually, looking at the CSV: row 1 has CUST NO.=1 with DEMAND=0, READY TIME=0,
    DUE DATE=1236, SERVICE TIME=0 — this is clearly the Depot.
    We remap it: Depot gets id=0, others keep their CUST NO. as-is but shifted.
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

                    # Gán giá vé theo category
                    if cat in FREE_CATEGORIES:
                        price = 0.0
                    else:
                        price = rng.choice(PRICE_OPTIONS)

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