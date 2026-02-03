class POI:
    def __init__(self, id, lat, lon, score, open_time, close_time, price, duration, category):
        self.id = id
        self.lat = lat
        self.lon = lon
        self.base_score = score  # DEMAND tương ứng trong Solomon
        self.open_time = open_time  # Giờ mở cửa (giờ thập phân)
        self.close_time = close_time  # Giờ đóng cửa (giờ thập phân)
        self.price = price  # Chi phí tham quan
        self.duration = duration # Thời gian tham quan (phút)
        self.category = category  # Loại điểm (culture, food, nature, shopping, ...)
