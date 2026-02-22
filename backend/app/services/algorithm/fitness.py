import math
from app.models.domain import POI
from app.models.schemas import UserPreferences


# =============================================================================
#  DISTANCE & TRAVEL TIME  (Euclidean – Solomon benchmark compatible)
# =============================================================================

def euclidean_distance(p1: POI, p2: POI) -> float:
    """Euclidean distance between two POIs in coordinate units."""
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)


def get_travel_time(p1: POI, p2: POI) -> float:
    """
    Travel time between two POIs.
    For Solomon benchmarks, travel time == Euclidean distance
    (speed = 1 unit/time‐unit).
    """
    return euclidean_distance(p1, p2)


# =============================================================================
#  CONSTRAINT CHECKING  (TOPTW feasibility)
# =============================================================================

def check_constraints(route: list[POI], user_prefs: UserPreferences) -> bool:
    """
    Validate whether a COMPLETE route [Depot, ..., Depot] satisfies all
    TOPTW constraints:
      1. Time Windows  – arrive at each POI before its close_time.
      2. Max Tour Time – return to depot before user_prefs.end_time (== depot close).
      3. Budget        – total price of visited POIs ≤ user_prefs.budget.
    
    Time is simulated forward from depot departure at user_prefs.start_time.
    If a vehicle arrives before open_time, it *waits* (no penalty, but time passes).

    Returns True if ALL constraints are satisfied, False otherwise.
    """
    if len(route) < 2:
        return False  # Must at least have [Depot, Depot]

    current_time = user_prefs.start_time  # Solomon time unit
    total_cost = 0.0

    for i in range(len(route) - 1):
        curr = route[i]
        next_p = route[i + 1]

        # --- Travel ---
        travel = get_travel_time(curr, next_p)
        arrival = current_time + travel

        # --- Time Window ---
        # Wait if arrived too early
        if arrival < next_p.open_time:
            arrival = next_p.open_time

        # Infeasible if arrived after closing
        if arrival > next_p.close_time:
            return False

        # --- Service ---
        departure = arrival + next_p.duration
        current_time = departure

        # --- Budget ---
        total_cost += next_p.price

    # Budget constraint
    if total_cost > user_prefs.budget:
        return False

    return True


def try_add_poi(route: list[POI], candidate: POI,
                user_prefs: UserPreferences) -> bool:
    """
    Check if `candidate` can be *inserted just before the trailing Depot*
    while keeping the route feasible.
    
    The route is assumed to be [Depot, ..., (last‐visited)] WITHOUT
    the trailing Depot yet (the depot is appended temporarily for checking).
    
    Returns True if the route [*route, candidate, Depot] satisfies constraints.
    """
    depot = route[0]  # Depot is always the first element
    test_route = route + [candidate, depot]
    return check_constraints(test_route, user_prefs)


# =============================================================================
#  FITNESS EVALUATION
# =============================================================================

def calculate_fitness(ind, user_prefs: UserPreferences) -> float:
    """
    Evaluate fitness of an Individual.

    Fitness = Σ (base_score x interest_weight) - penalties.

    Penalties cover:
      • Time-window violation
      • Budget overrun
      • Late return to depot
    """
    current_time = user_prefs.start_time
    total_score = 0.0
    total_cost = 0.0
    penalty = 0.0

    for i in range(len(ind.route) - 1):
        curr = ind.route[i]
        next_p = ind.route[i + 1]

        # --- Score (skip depot; its category is 'depot') ---
        w = user_prefs.interest_weights.get(curr.category, 0.0)
        total_score += curr.base_score * w
        total_cost += curr.price

        # --- Travel ---
        travel = get_travel_time(curr, next_p)
        arrival = current_time + travel

        # --- Time Window ---
        if arrival < next_p.open_time:
            arrival = next_p.open_time  # Wait

        if arrival > next_p.close_time:
            over = arrival - next_p.close_time
            penalty += over * 100  # Heavy penalty for late arrival

        # --- Service ---
        departure = arrival + next_p.duration
        current_time = departure

    # Budget penalty
    if total_cost > user_prefs.budget:
        penalty += (total_cost - user_prefs.budget) * 0.5

    # Late return penalty (check against depot close_time or user end_time)
    end_time_limit = user_prefs.end_time
    if current_time > end_time_limit:
        penalty += (current_time - end_time_limit) * 100

    ind.fitness = total_score - penalty
    ind.total_score = total_score
    ind.total_cost = total_cost
    ind.total_time = current_time

    return ind.fitness