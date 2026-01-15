import json
import os
from app.models.domain import POI

def load_pois():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    file_path = os.path.join(base_dir, 'data', 'mock_pois.json')

    with open(file_path, 'r') as f:
        data = json.load(f)

    pois = []
    for item in data:
        pois.append(POI(**item))
    return pois