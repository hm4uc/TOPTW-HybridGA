import os
import csv
import random
from app.models.domain import POI

# --- DANH SÁCH CATEGORY CHUẨN ---
# Dùng bộ này cho toàn bộ hệ thống
CATEGORIES = [
    'history_culture', # Lăng Bác, Văn Miếu, Hoàng Thành, Chùa Một Cột, ...
    'nature_parks', # Công viên Thống Nhất, Hồ Gươm, Vườn hoa Lý Thái Tổ, ...
    'food_drink', # Phở Thìn, Bún Chả Hương Liên, Cà phê Giảng, ...
    'shopping', # Chợ Đồng Xuân, Vincom Bà Triệu, Tràng Tiền Plaza, ...
    'entertainment' # Rạp chiếu phim Quốc gia, Nhà hát Lớn Hà Nội, Cung Văn hóa Hữu nghị Việt Xô, ...
]

# Tỷ lệ xuất hiện giả lập (Mô phỏng đặc thù du lịch Hà Nội)
# history_culture: 35%, food: 25%, nature: 15%, shopping: 15%, entertainment: 10%
CATEGORY_WEIGHTS = [0.35, 0.15, 0.25, 0.15, 0.10]

def load_solomon_data():
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    file_path = os.path.join(os.getcwd(), 'data', 'C101.csv')

    pois = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f: # Thêm encoding utf-8 cho chắc
            reader = csv.DictReader(f)
            for row in reader:
                pid = int(row.get('CUST NO.', 0))

                # --- LOGIC GÁN TAG ---
                # 1. Điểm 0 luôn là Depot (Khách sạn)
                if pid == 0:
                    cat = "depot"
                else:
                    # 2. Các điểm khác gán theo tỷ lệ weights đã định nghĩa
                    # Dùng seed theo PID để đảm bảo Node 1 luôn là 'history_culture' mỗi lần chạy lại
                    random.seed(pid)
                    cat = random.choices(CATEGORIES, weights=CATEGORY_WEIGHTS, k=1)[0]

                poi = POI(
                    id=pid,
                    x=float(row.get('XCOORD.', 0)),
                    y=float(row.get('YCOORD.', 0)),
                    score=float(row.get('DEMAND', 0)),
                    open_time=float(row.get('READY TIME', 0)),
                    close_time=float(row.get('DUE DATE', 0)),
                    duration=float(row.get('SERVICE TIME', 0)),
                    category=cat
                )
                pois.append(poi)
    except Exception as e:
        print(f"Lỗi đọc file data: {e}")
        return []

    return pois