from __future__ import annotations
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from receptor_agent.techcards_v2.schemas import TechCardV2

def techcard_to_pdf(card: TechCardV2) -> bytes:
    bio = BytesIO()
    c = canvas.Canvas(bio, pagesize=A4)
    w, h = A4
    y = h - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, f"Техкарта: {card.meta.name}")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Категория: {card.meta.category or '-'}   Кухня: {card.meta.cuisine or '-'}")
    y -= 20
    c.drawString(40, y, f"Выход: {card.yield_.portions} x {card.yield_.per_portion_g} г = {card.yield_.total_net_g} г")
    y -= 30
    c.setFont("Helvetica-Bold", 11); c.drawString(40, y, "Состав:"); y -= 18; c.setFont("Helvetica", 10)
    for ing in card.ingredients:
        line = f"- {ing.canonical or ing.name}: брутто {ing.gross_g:.1f} г → нетто {ing.net_g:.1f} г (потери {ing.loss_pct:.1f}%)"
        c.drawString(40, y, line); y -= 14
        if y < 80:
            c.showPage(); y = h - 40; c.setFont("Helvetica", 10)
    y -= 10
    c.setFont("Helvetica-Bold", 11); c.drawString(40, y, "Процесс:"); y -= 18; c.setFont("Helvetica", 10)
    for step in card.process:
        tail = []
        if step.time_min: tail.append(f"~{step.time_min} мин")
        if step.temp_c:   tail.append(f"{step.temp_c}°C")
        info = f" ({', '.join(tail)})" if tail else ""
        c.drawString(40, y, f"{step.step}. {step.desc}{info}"); y -= 14
        if y < 80:
            c.showPage(); y = h - 40; c.setFont("Helvetica", 10)
    y -= 10
    c.setFont("Helvetica-Bold", 11); c.drawString(40, y, "HACCP:"); y -= 18; c.setFont("Helvetica", 10)
    for ccp in card.haccp.ccp:
        line = f"- {ccp.name}: лимит {ccp.limit}; мониторинг: {ccp.monitoring}; корректирующие: {ccp.corrective}"
        c.drawString(40, y, line); y -= 14
        if y < 80:
            c.showPage(); y = h - 40; c.setFont("Helvetica", 10)
    c.showPage(); c.save()
    return bio.getvalue()