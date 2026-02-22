"""
Population Initialization for the Hybrid Genetic Algorithm (HGA).

Implements two strategies from Botelho et al. (2010) and Labadie et al. (2012):
  • Strategy 1 – Randomized Insertion Heuristic  (80% of population, 40 individuals)
  • Strategy 2 – Pure Random Initialization        (20% of population, 10 individuals)

Total population size: 50 (fixed).
"""

import random
import math
from typing import List

from app.models.domain import POI, Individual
from app.models.schemas import UserPreferences
from app.services.algorithm.fitness import (
    euclidean_distance,
    try_add_poi,
)


# ─── Constants ───────────────────────────────────────────────────────────────
POPULATION_SIZE = 50
HEURISTIC_COUNT = 40   # 80%  → Randomized Insertion Heuristic
RANDOM_COUNT    = 10   # 20%  → Pure Random
RCL_SIZE        = 3    # Top-k candidates in Restricted Candidate List


# =============================================================================
#  Strategy 1: Randomized Insertion Heuristic  (Labadie desirability ratio)
# =============================================================================

def _labadie_ratio(poi: POI, current_location: POI,
                   user_prefs: UserPreferences) -> float:
    """
    Labadie desirability ratio:
        ratio = (POI.score × interest_weight) / distance(current, POI)

    Higher ratio → more desirable candidate.
    If distance == 0, return +inf to strongly favour that POI.
    """
    interest_weight = user_prefs.interest_weights.get(poi.category, 0.0)
    numerator = poi.base_score * interest_weight

    dist = euclidean_distance(current_location, poi)
    if dist == 0:
        return float('inf')

    return numerator / dist


def _create_heuristic_individual(
    pois: List[POI],
    depot: POI,
    user_prefs: UserPreferences,
) -> Individual:
    """
    Build ONE individual using the Randomized Insertion Heuristic:
      1. Start with route = [Depot].
      2. Maintain a set of unvisited POIs (all non-depot POIs).
      3. Repeat:
         a. Filter unvisited POIs → keep only those passing `try_add_poi`.
         b. Compute Labadie ratio for each valid candidate.
         c. Sort descending → build RCL from Top-k.
         d. Pick one random POI from the RCL → append to route.
      4. When no more valid POIs can be added, append Depot and return.
    """
    route: List[POI] = [depot]
    unvisited = {p.id for p in pois if p.id != depot.id}
    poi_map = {p.id: p for p in pois}

    while unvisited:
        current = route[-1]

        # --- Filter: only POIs that can be feasibly inserted ---
        candidates = []
        for pid in list(unvisited):
            poi = poi_map[pid]
            if try_add_poi(route, poi, user_prefs):
                ratio = _labadie_ratio(poi, current, user_prefs)
                candidates.append((poi, ratio))

        if not candidates:
            break  # No feasible POI left

        # --- Sort by desirability ratio (descending) ---
        candidates.sort(key=lambda x: x[1], reverse=True)

        # --- Restricted Candidate List (Top-k) ---
        rcl = candidates[:RCL_SIZE]

        # --- Random pick from RCL ---
        chosen_poi, _ = random.choice(rcl)

        route.append(chosen_poi)
        unvisited.discard(chosen_poi.id)

    # Close route at Depot
    route.append(depot)
    return Individual(route=route)


# =============================================================================
#  Strategy 2: Pure Random Initialization
# =============================================================================

def _create_random_individual(
    pois: List[POI],
    depot: POI,
    user_prefs: UserPreferences,
) -> Individual:
    """
    Build ONE individual using Pure Random insertion:
      1. Start with route = [Depot].
      2. Shuffle all non-depot POIs randomly.
      3. Iterate: if adding the POI satisfies constraints, append it.
      4. When done, append Depot and return.
    """
    route: List[POI] = [depot]
    candidates = [p for p in pois if p.id != depot.id]
    random.shuffle(candidates)

    for poi in candidates:
        if try_add_poi(route, poi, user_prefs):
            route.append(poi)

    # Close route at Depot
    route.append(depot)
    return Individual(route=route)


# =============================================================================
#  PUBLIC API: Generate Full Initial Population
# =============================================================================

def initialize_population(
    pois: List[POI],
    user_prefs: UserPreferences,
) -> List[Individual]:
    """
    Generate the initial population of 50 individuals:
      • 40 via Randomized Insertion Heuristic  (high quality + diversity)
      • 10 via Pure Random                     (exploration / diversity)

    Every route is guaranteed to:
      ✓ Start and end at the Depot (POI id == 0)
      ✓ Pass check_constraints before any POI is appended

    Parameters
    ----------
    pois : list[POI]
        All available Points of Interest (including the depot at index 0).
    user_prefs : UserPreferences
        User constraints (budget, time window, interests).

    Returns
    -------
    list[Individual]
        Population of size 50.
    """
    depot = next((p for p in pois if p.id == 0), None)
    if depot is None:
        raise ValueError("Depot (POI id=0) not found in the POI list.")

    population: List[Individual] = []

    # --- Strategy 1: Heuristic individuals ---
    for i in range(HEURISTIC_COUNT):
        ind = _create_heuristic_individual(pois, depot, user_prefs)
        population.append(ind)

    # --- Strategy 2: Random individuals ---
    for i in range(RANDOM_COUNT):
        ind = _create_random_individual(pois, depot, user_prefs)
        population.append(ind)

    assert len(population) == POPULATION_SIZE, (
        f"Expected {POPULATION_SIZE} individuals, got {len(population)}"
    )

    # --- Summary log ---
    heuristic_lens = [len(ind.route) for ind in population[:HEURISTIC_COUNT]]
    random_lens = [len(ind.route) for ind in population[HEURISTIC_COUNT:]]
    print(f"[Init] Population created: {POPULATION_SIZE} individuals")
    print(f"       Heuristic ({HEURISTIC_COUNT}): avg route length = "
          f"{sum(heuristic_lens)/len(heuristic_lens):.1f}")
    print(f"       Random    ({RANDOM_COUNT}):  avg route length = "
          f"{sum(random_lens)/len(random_lens):.1f}")

    return population
