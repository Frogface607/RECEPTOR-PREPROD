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
            card.meta.title, "",  # category не используется в V2
            ing.canonical_id or ing.name, ing.unit,
            ing.brutto_g, ing.netto_g, ing.loss_pct,
            card.yield_.perPortion_g, 1  # portions не используется в V2
        ])
        row += 1
    wb.close()
    return bio.getvalue()