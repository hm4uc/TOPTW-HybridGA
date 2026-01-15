class POI:
    def __init__(self, id, name, lat, lon, score, open_time, close_time, price, category):
        self.id = id
        self.name = name
        self.lat = lat
        self.lon = lon
        self.base_score = score
        self.open_time = open_time
        self.close_time = close_time
        self.price = price
        self.category = category

class Individual:
    def __init__(self, route):
        self.route = route # List[POI]
        self.fitness = 0.0
        self.total_score = 0.0
        self.total_cost = 0.0
        self.total_time = 0.0
        self.penalty = 0.0