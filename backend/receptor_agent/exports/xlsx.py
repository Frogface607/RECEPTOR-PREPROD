from __future__ import annotations
from io import BytesIO
import xlsxwriter
from receptor_agent.techcards_v2.schemas import TechCardV2

def techcard_to_xlsx(card: TechCardV2) -> bytes:
    bio = BytesIO()
    wb = xlsxwriter.Workbook(bio, {'in_memory': True})
    ws = wb.add_worksheet("TechCard")
    headers = ["dish_name","category","ingredient","uom","gross_g","net_g","loss_pct","portion_g","portions"]
    for i,h in enumerate(headers):
        ws.write(0, i, h)
    row = 1
    for ing in card.ingredients:
        ws.write_row(row, 0, [
            card.meta.name, card.meta.category or "",
            ing.canonical or ing.name, ing.uom,
            ing.gross_g, ing.net_g, ing.loss_pct,
            card.yield_.per_portion_g, card.yield_.portions
        ])
        row += 1
    wb.close()
    return bio.getvalue()