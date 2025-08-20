from __future__ import annotations
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from receptor_agent.techcards_v2.schemas import TechCardV2
from typing import Optional, Dict, Any

def techcard_to_pdf(card: TechCardV2, use_operational_rounding: bool = True) -> bytes:
    """
    E. Operational Rounding v1: Генерация PDF с операционным округлением
    
    Args:
        card: Техкарта TechCardV2
        use_operational_rounding: Применять операционное округление для отображения
        
    Returns:
        PDF в байтах
    """
    bio = BytesIO()
    c = canvas.Canvas(bio, pagesize=A4)
    w, h = A4
    y = h - 40
    
    # Применяем operational rounding если нужно
    working_card = card
    rounding_applied = False
    
    if use_operational_rounding:
        try:
            from receptor_agent.techcards_v2.operational_rounding import get_operational_rounder
            rounder = get_operational_rounder()
            
            # Конвертируем в dict для округления
            card_dict = card.model_dump()
            rounding_result = rounder.round_techcard_ingredients(card_dict)
            
            # Создаем TechCardV2 с округленными данными
            working_card = TechCardV2.model_validate(rounding_result['rounded_techcard'])
            rounding_applied = True
            
        except Exception as e:
            print(f"Warning: Could not apply operational rounding to PDF: {e}")
            # Продолжаем с исходной техкартой
    
    # Заголовок
    c.setFont("Helvetica-Bold", 14)
    title = getattr(working_card.meta, 'title', 'Техническая карта')
    c.drawString(40, y, f"Техкарта: {title}")
    y -= 20
    
    # Мета информация
    c.setFont("Helvetica", 10)
    cuisine = getattr(working_card.meta, 'cuisine', None)
    tags = getattr(working_card.meta, 'tags', [])
    version = getattr(working_card.meta, 'version', '2.0')
    
    c.drawString(40, y, f"Версия: {version}   Кухня: {cuisine or '-'}   Теги: {', '.join(tags) if tags else '-'}")
    y -= 20
    
    # Выход
    yield_info = working_card.yield_
    portions = getattr(working_card, 'portions', 1)
    per_portion = yield_info.perPortion_g
    per_batch = yield_info.perBatch_g
    
    c.drawString(40, y, f"Выход: {portions} порц. x {per_portion:.0f} г = {per_batch:.0f} г")
    
    if rounding_applied:
        c.setFont("Helvetica", 8)
        y -= 12
        c.drawString(40, y, "* Количества округлены для удобства производства")
        c.setFont("Helvetica", 10)
    
    y -= 30
    
    # Ингредиенты
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Состав:")
    y -= 18
    c.setFont("Helvetica", 10)
    
    for ing in working_card.ingredients:
        # Получаем округленные или точные значения
        brutto_g = getattr(ing, 'brutto_g', 0)
        netto_g = getattr(ing, 'netto_g', 0)
        loss_pct = getattr(ing, 'loss_pct', 0)
        unit = getattr(ing, 'unit', 'г')
        
        # Форматируем количества без лишних десятичных знаков
        brutto_str = f"{brutto_g:g}" if brutto_g == int(brutto_g) else f"{brutto_g:.1f}"
        netto_str = f"{netto_g:g}" if netto_g == int(netto_g) else f"{netto_g:.1f}"
        
        line = f"- {ing.name}: брутто {brutto_str} {unit} → нетто {netto_str} {unit} (потери {loss_pct:.1f}%)"
        c.drawString(40, y, line)
        y -= 14
        
        if y < 100:
            c.showPage()
            y = h - 40
            c.setFont("Helvetica", 10)
    
    y -= 10
    
    # Технологический процесс
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Технологический процесс:")
    y -= 18
    c.setFont("Helvetica", 10)
    
    for step in working_card.process:
        # Дополнительная информация о шаге
        details = []
        if hasattr(step, 'time_min') and step.time_min:
            details.append(f"{step.time_min} мин")
        if hasattr(step, 'temp_c') and step.temp_c:
            details.append(f"{step.temp_c}°C")
        if hasattr(step, 'equipment') and step.equipment:
            equipment = step.equipment if isinstance(step.equipment, list) else [step.equipment]
            details.append(f"Оборудование: {', '.join(equipment)}")
        
        info = f" ({'; '.join(details)})" if details else ""
        
        step_n = getattr(step, 'n', '')
        action = getattr(step, 'action', 'Действие не указано')
        
        c.drawString(40, y, f"{step_n}. {action}{info}")
        y -= 14
        
        if y < 100:
            c.showPage()
            y = h - 40
            c.setFont("Helvetica", 10)
    
    y -= 10
    
    # Хранение
    if hasattr(working_card, 'storage') and working_card.storage:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, "Условия хранения:")
        y -= 18
        c.setFont("Helvetica", 10)
        
        storage = working_card.storage
        conditions = getattr(storage, 'conditions', 'Не указано')
        shelf_life = getattr(storage, 'shelfLife_hours', 0)
        serving_temp = getattr(storage, 'servingTemp_c', None)
        
        c.drawString(40, y, f"Условия: {conditions}")
        y -= 14
        c.drawString(40, y, f"Срок годности: {shelf_life} часов")
        if serving_temp:
            y -= 14
            c.drawString(40, y, f"Температура подачи: {serving_temp}°C")
    
    c.showPage()
    c.save()
    return bio.getvalue()