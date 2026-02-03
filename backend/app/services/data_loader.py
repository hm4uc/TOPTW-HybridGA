import os
from app.models.domain import POI

# Danh sách category giả lập
CATEGORIES = ['history', 'culture', 'nature', 'food', 'shopping']

def load_solomon_c101():
    base_path = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
    file_path = os.path.join(base_path, 'data', 'solomon_instances', 'C101.csv')

    pois = []

    try:
        with open(file_path) as csvfile:
            lines = csvfile.readlines()[1:]  # Bỏ qua header
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) < 9:
                    continue

                id = int(parts[0])
                lat = float(parts[1])
                lon = float(parts[2])
                score = float(parts[3])
                open_time = float(parts[4])
                close_time = float(parts[5])
                price = float(parts[6])
                duration = int(parts[7])

                # Gán category ngẫu nhiên từ danh sách giả lập
                category = CATEGORIES[id % len(CATEGORIES)]

                poi = POI(id, lat, lon, score, open_time, close_time, price, duration, category)
                pois.append(poi)
    except Exception as e:
        print(f"Error loading Solomon C101 data: {e}")
        return []

    return pois