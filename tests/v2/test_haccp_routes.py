import os
os.environ.setdefault("FEATURE_TECHCARDS_V2", "true")

from fastapi.testclient import TestClient
from receptor_agent.server import app
from receptor_agent.llm.pipeline import run_pipeline, ProfileInput

def test_haccp_generate_and_audit():
    client = TestClient(app)
    card = run_pipeline(ProfileInput(name="EDISON", cuisine="итальянская")).card.model_dump(by_alias=True)

    g = client.post("/api/v1/haccp.v2/generate", json=card)
    assert g.status_code == 200
    tc = g.json()
    assert tc["haccp"]["hazards"]

    a = client.post("/api/v1/haccp.v2/audit", json=tc)
    assert a.status_code == 200
    audit = a.json()
    assert "issues" in audit and "patch" in audit