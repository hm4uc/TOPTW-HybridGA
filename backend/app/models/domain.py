class POI:
    """
    Represents a Point of Interest (or Depot when id == 0).
    Coordinates use Euclidean x/y matching Solomon benchmark format.
    Time fields are in Solomon's integer time units.
    """

    def __init__(self, id: int, x: float, y: float, score: float,
                 open_time: float, close_time: float,
                 duration: float, category: str, price: float = 0.0):
        self.id = id
        self.x = x                  # Tọa độ X (Euclidean – Solomon)
        self.y = y                  # Tọa độ Y (Euclidean – Solomon)
        self.base_score = score     # DEMAND tương ứng trong Solomon
        self.open_time = open_time  # Giờ mở cửa (đơn vị thời gian Solomon)
        self.close_time = close_time  # Giờ đóng cửa (đơn vị thời gian Solomon)
        self.price = price          # Chi phí tham quan
        self.duration = duration    # Thời gian tham quan (đơn vị thời gian Solomon = SERVICE TIME)
        self.category = category    # Loại điểm (depot, history_culture, food_drink, ...)

    def __repr__(self):
        return f"POI(id={self.id}, cat={self.category}, score={self.base_score})"


class Individual:
    """
    Represents a single solution (chromosome) in the GA population.
    A route is an ordered list of POI objects: [Depot, POI_a, POI_b, ..., Depot].
    """

    def __init__(self, route: list[POI] = None):
        self.route: list[POI] = route if route is not None else []
        self.fitness: float = 0.0
        self.total_score: float = 0.0
        self.total_cost: float = 0.0
        self.total_time: float = 0.0
        self.total_wait: float = 0.0   # Tổng thời gian chờ tại các POI

    def __repr__(self):
        ids = [p.id for p in self.route]
        return f"Individual(fitness={self.fitness:.2f}, route_ids={ids})"

    def __len__(self):
        return len(self.route)
