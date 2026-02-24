import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app.services.data_loader import load_solomon_c101

pois = load_solomon_c101()

print("--- Sample POIs (first 15) ---")
for p in pois[:15]:
    print(f"  id={p.id:3d}  cat={p.category:17s}  price={p.price:>10.0f}")

free = sum(1 for p in pois if p.price == 0)
paid = sum(1 for p in pois if p.price > 0)
print(f"\nFree entry: {free}  |  Paid entry: {paid}")

from collections import Counter
price_dist = Counter(p.price for p in pois if p.price > 0)
print(f"Paid price distribution: {dict(price_dist)}")
