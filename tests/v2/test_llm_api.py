import os
os.environ.setdefault("FEATURE_TECHCARDS_V2", "true")

from fastapi.testclient import TestClient
import sys
sys.path.append("/app/backend")
from server import app

def test_status_endpoint():
    client = TestClient(app)
    r = client.get("/api/v1/techcards.v2/status")
    assert r.status_code == 200
    data = r.json()
    assert "feature_enabled" in data
    assert "llm_enabled" in data
    assert data["feature_enabled"] is True

def test_generate_with_llm_flag():
    client = TestClient(app)
    payload = {"name":"EDISON","cuisine":"французская","equipment":["oven"],"budget":400.0,"dietary":[]}
    
    # Test with use_llm=false (should work)
    r = client.post("/api/v1/techcards.v2/generate?use_llm=false", json=payload)
    assert r.status_code == 200
    card = r.json()
    assert card["meta"]["name"]
    assert card["yield"]["total_net_g"] > 0
    
    # Test with use_llm=true (should fallback to local if no key)
    r2 = client.post("/api/v1/techcards.v2/generate?use_llm=true", json=payload)  
    assert r2.status_code == 200
    card2 = r2.json()
    assert card2["meta"]["name"]