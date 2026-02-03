import math

# Hàm phụ trợ: Tính khoảng cách Haversine (km) -> quy ra phút
def get_travel_time(p1, p2):
    R = 6371  # Bán kính trái đất (km)
    dlat = math.radians(p2.lat - p1.lat)
    dlon = math.radians(p2.lon - p1.lon)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(p1.lat)) * math.cos(math.radians(p2.lat)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    dist_km = R * c
    speed_kmh = 20 # Giả định tốc độ trung bình trong phố
    return (dist_km / speed_kmh) * 60 # phút

def calculate_fitness(ind, user_prefs):
    current_time = user_prefs.start_time * 60 # Đổi ra phút
    end_time_limit = user_prefs.end_time * 60

    total_score = 0
    total_cost = 0
    penalty = 0

    # Duyệt qua lộ trình
    for i in range(len(ind.route) - 1):
        curr = ind.route[i]
        next_p = ind.route[i+1]

        # 1. Tính Score theo sở thích
        w = user_prefs.interests.get(curr.category, 1.0)
        total_score += curr.base_score * w
        total_cost += curr.price

        # 2. Di chuyển
        travel = get_travel_time(curr, next_p)
        arrival = current_time + travel

        # 3. Check Time Window
        open_min = next_p.open_time * 60
        close_min = next_p.close_time * 60

        if arrival < open_min:
            wait = open_min - arrival
            arrival = open_min # Phải chờ đến khi mở cửa
        else:
            wait = 0

        if arrival > close_min:
            # Phạt nặng nếu đến muộn
            over = arrival - close_min
            penalty += over * 100

            # Thời gian tham quan (giả sử 60p)
        leave = arrival + 60
        current_time = leave

    # 4. Phạt ngân sách
    if total_cost > user_prefs.budget:
        penalty += (total_cost - user_prefs.budget) * 0.5

    # 5. Phạt quá giờ về
    if current_time > end_time_limit:
        penalty += (current_time - end_time_limit) * 100

    ind.fitness = total_score - penalty
    ind.total_score = total_score
    ind.total_cost = total_cost
    ind.total_time = current_time

    return ind.fitness