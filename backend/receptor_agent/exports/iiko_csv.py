from __future__ import annotations
from io import StringIO
import csv
from receptor_agent.techcards_v2.schemas import TechCardV2

# Минимальный CSV под ручной перенос в iiko Office:
# одна строка на ингредиент блюда, с полями блюда/выхода.
def techcard_to_csv(card: TechCardV2) -> str:
    buf = StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["dish_name","category","ingredient","uom","gross_g","net_g","loss_pct","portion_g","portions"])
    for ing in card.ingredients:
        w.writerow([
            card.meta.name,
            card.meta.category or "",
            ing.canonical or ing.name,
            ing.uom,
            f"{ing.gross_g:.2f}",
            f"{ing.net_g:.2f}",
            f"{ing.loss_pct:.2f}",
            card.yield_.per_portion_g,
            card.yield_.portions,
        ])
    return buf.getvalue()