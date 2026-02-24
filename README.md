# Thuật toán Hybrid GA cho bài toán TOPTW - Lập lịch trình du lịch cá nhân hóa

## Giới thiệu

Mã nguồn Khóa luận tốt nghiệp: **"Xây dựng hệ thống lập lịch trình du lịch theo ngữ cảnh dựa trên thuật toán di truyền lai (Hybrid GA)"**.

Hệ thống giải bài toán **Team Orienteering Problem with Time Windows (TOPTW)** theo hướng cá nhân hóa. Thay vì dùng điểm số tĩnh, thuật toán tối ưu lộ trình dựa trên sở thích cá nhân (User-Dependent Scores), ngân sách và ràng buộc thời gian của người dùng.

## Tính năng chính

- **Tối ưu theo sở thích**: Tối đa hóa tổng điểm dựa trên mức quan tâm của người dùng với 5 loại hình (Lịch sử - Văn hóa, Thiên nhiên, Ẩm thực, Mua sắm, Giải trí).
- **Thuật toán di truyền lai (HGA)**:
  - Giải thuật Di truyền (GA) cho khám phá không gian nghiệm toàn cục.
  - Tìm kiếm cục bộ 2-opt (Smart Mutation) để hội tụ nhanh và tinh chỉnh tuyến đường.
  - Insertion Mutation để chèn POI mới, tăng điểm từ thời gian dư.
  - Smart Repair loại bỏ POI có tỷ lệ Score/Time kém nhất khi vi phạm ràng buộc.
- **Xử lý ràng buộc cứng**: Ngân sách, khung giờ chuyến đi (Start/End time), cửa sổ thời gian (Opening/Closing hours) của từng POI.
- **Khởi tạo quần thể 2 chiến lược**: 80% Randomized Insertion Heuristic (Labadie ratio), 20% Pure Random.
- **Ứng dụng di động đa nề tảng**: Flutter hiển thị lộ trình trên Google Maps.

## Công nghệ sử dụng

### Backend

| Thành phần | Chi tiết |
|---|---|
| Ngôn ngữ | Python 3.13 |
| Framework | FastAPI |
| Thư viện | NumPy, Pandas, Pydantic, Uvicorn |
| Thuật toán | Hybrid GA tự triển khai theo OOP |
| Dữ liệu | Solomon Benchmark C101 (CSV) |

### Mobile

| Thành phần | Chi tiết |
|---|---|
| Framework | Flutter (Dart), SDK ^3.10 |
| Bản đồ | Google Maps SDK |

## Cấu trúc thư mục

```
TOPTW-HybridGA/
├── backend/
│   ├── app/
│   │   ├── main.py                  # Entry point, khởi tạo FastAPI
│   │   ├── api/
│   │   │   └── routes.py            # API endpoint /api/optimize
│   │   ├── models/
│   │   │   ├── domain.py            # Lớp POI, Individual
│   │   │   └── schemas.py           # Request/Response schemas (Pydantic)
│   │   └── services/
│   │       ├── data_loader.py       # Đọc và cache dữ liệu Solomon C101
│   │       └── algorithm/
│   │           ├── hga_engine.py    # Vòng lặp chính HGA (Selection, Crossover, Mutation, Repair)
│   │           ├── initialization.py # Khởi tạo quần thể (Heuristic + Random)
│   │           ├── fitness.py       # Hàm fitness, kiểm tra ràng buộc, ma trận khoảng cách
│   │           └── mutation.py      # 2-opt Local Search (Smart Mutation)
│   ├── data/
│   │   └── solomon_instances/       # Bộ dữ liệu benchmark (C101.csv, C102.csv, RC101.csv)
│   └── requirements.txt
├── mobile/                          # Ứng dụng Flutter
│   ├── lib/
│   │   └── main.dart
│   └── pubspec.yaml
├── references/                      # Tài liệu tham khảo (PDF)
├── LICENSE
└── README.md
```

## API

### POST /api/optimize

**Request Body:**

```json
{
  "budget": 500000,
  "start_time": 8.0,
  "end_time": 17.0,
  "start_node_id": 0,
  "interests": {
    "history_culture": 5,
    "nature_parks": 3,
    "food_drink": 4,
    "shopping": 1,
    "entertainment": 2
  }
}
```

**Response:** Trả về lộ trình tối ưu gồm tổng điểm, tổng chi phí, tổng thời gian, thời gian chạy thuật toán và danh sách các điểm tham quan theo thứ tự (bao gồm thời gian đến, chờ, bắt đầu, rời đi tại mỗi điểm).

## Cài đặt và chạy

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Server chạy tại `http://localhost:8000`. Tài liệu API tự động tại `http://localhost:8000/docs`.

### Mobile

```bash
cd mobile
flutter pub get
flutter run
```

## Giấy phép

Phân phối theo giấy phép MIT. Xem file LICENSE để biết thêm chi tiết.

**Tác giả:** Hoàng Minh Đức

**Khoa Công nghệ Thông tin - Đại học Công nghệ, ĐHQGHN**
