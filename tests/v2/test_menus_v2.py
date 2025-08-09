import os
os.environ.setdefault("FEATURE_TECHCARDS_V2", "true")

from fastapi.testclient import TestClient
import sys
sys.path.append("/app/backend")
from server import app

def test_generate_replace_export_menu_v2():
    client = TestClient(app)
    payload = {"name":"EDISON","cuisine":"мексиканская","equipment":["oven"],"budget":350.0,"dietary":[]}
    r = client.post("/api/v1/menus.v2/generate?courses=5", json=payload)
    assert r.status_code == 200, r.text
    menu = r.json()
    assert menu["menuId"] and len(menu["items"]) == 5

    # replace индекс 0
    rep = client.post(f"/api/v1/menus.v2/{menu['menuId']}/replace?index=0", json=payload)
    assert rep.status_code == 200
    new_item = rep.json()
    assert new_item["meta"]["name"]

    # export zip
    ex = client.get(f"/api/v1/menus.v2/{menu['menuId']}/export")
    assert ex.status_code == 200
    assert ex.headers["content-type"] == "application/zip"
    assert len(ex.content) > 3000