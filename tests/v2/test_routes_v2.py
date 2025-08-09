import os
os.environ.setdefault("FEATURE_TECHCARDS_V2", "true")

from fastapi.testclient import TestClient

# Импортируем app из server.py, а не main.py  
import sys
sys.path.append("/app/backend")
from server import app

def test_generate_and_export_v2():
    client = TestClient(app)
    payload = {
        "name": "EDISON",
        "cuisine": "мексиканская",
        "equipment": ["oven"],
        "budget": 350.0,
        "dietary": []
    }
    r = client.post("/api/v1/techcards.v2/generate", json=payload)
    assert r.status_code == 200, r.text
    card = r.json()
    assert card["meta"]["name"]
    ex = client.post("/api/v1/techcards.v2/export", json=card)
    assert ex.status_code == 200
    assert ex.headers["content-type"] == "application/zip"
    assert len(ex.content) > 1200