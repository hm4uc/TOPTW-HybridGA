"""
Quick smoke test for Population Initialization.
Run from backend/ directory:  python test_initialization.py
"""
import sys
import os

# Ensure the backend/app package is importable
sys.path.insert(0, os.path.dirname(__file__))

from app.models.schemas import UserPreferences
from app.services.algorithm.hga_engine import HybridGeneticAlgorithm

# --- Build user preferences matching the Solomon C101 time horizon ---
user_prefs = UserPreferences(
    budget=999999,           # Effectively no budget constraint for testing
    start_time=0,            # Solomon depot opens at time 0
    end_time=1236,           # Solomon depot closes at time 1236
    start_node_id=0,
    interests={
        "history_culture": 4,   # 4 sao → w = 1.5  (quan tâm nhiều)
        "nature_parks":    3,   # 3 sao → w = 1.0  (trung bình)
        "food_drink":      4,   # 4 sao → w = 1.5  (quan tâm nhiều)
        "shopping":        2,   # 2 sao → w = 0.5  (ít quan tâm)
        "entertainment":   3,   # 3 sao → w = 1.0  (trung bình)
    },
)

hga = HybridGeneticAlgorithm(user_prefs)
population = hga.initialize_population()

print("\n" + "=" * 70)
print("INITIALIZATION VALIDATION")
print("=" * 70)

# 1. Population size check
assert len(population) == 50, f"FAIL: Population size = {len(population)}, expected 50"
print(f"[OK] Population size: {len(population)}")

# 2. Every route starts and ends at Depot
for i, ind in enumerate(population):
    assert ind.route[0].id == 0, f"FAIL: Individual {i} does not start at Depot"
    assert ind.route[-1].id == 0, f"FAIL: Individual {i} does not end at Depot"
print("[OK] All routes start and end at Depot (id=0)")

# 3. No duplicate POIs within a route (except Depot which appears twice)
for i, ind in enumerate(population):
    interior = [p.id for p in ind.route[1:-1]]
    assert len(interior) == len(set(interior)), (
        f"FAIL: Duplicate POIs in individual {i}: {interior}"
    )
print("[OK] No duplicate POIs in any route (interior)")

# 4. Routes have meaningful length (not just [Depot, Depot])
avg_len = sum(len(ind.route) for ind in population) / len(population)
print(f"[OK] Average route length: {avg_len:.1f} POIs (including 2 depots)")

# 5. Show top 5 and bottom 5
print("\n--- Top 5 individuals ---")
for ind in population[:5]:
    route_ids = [p.id for p in ind.route]
    print(f"  fitness={ind.fitness:8.2f}  |  route ({len(ind.route)} nodes): {route_ids}")

print("\n--- Bottom 5 individuals ---")
for ind in population[-5:]:
    route_ids = [p.id for p in ind.route]
    print(f"  fitness={ind.fitness:8.2f}  |  route ({len(ind.route)} nodes): {route_ids}")

print("\n=== ALL CHECKS PASSED ===")
