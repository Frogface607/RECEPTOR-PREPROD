from __future__ import annotations
from datetime import datetime
from receptor_agent.techcards_v2.schemas import TechCardV2

def generate_print_html(card: TechCardV2, status: str = "success", issues: list = None) -> str:
    """Генерация HTML для ГОСТ-печати A4 техкарты"""
    if issues is None:
        issues = []
    
    # Водяной знак для статуса
    watermark_html = ""
    if status == "draft":
        watermark_html = '<div class="watermark">ЧЕРНОВИК</div>'
    
    # Формируем таблицу ингредиентов
    ingredients_html = ""
    total_netto = 0.0
    
    for ing in card.ingredients:
        allergens_text = ", ".join(ing.allergens) if ing.allergens else "—"
        
        ingredients_html += f"""
        <tr>
            <td>{ing.name}</td>
            <td>{ing.brutto_g:.1f}</td>
            <td>{ing.loss_pct:.1f}</td>
            <td>{ing.netto_g:.1f}</td>
            <td>{ing.unit}</td>
        </tr>
        """
        total_netto += ing.netto_g
    
    # Итоговая строка ингредиентов
    ingredients_html += f"""
    <tr class="total-row">
        <td><strong>ИТОГО по нетто:</strong></td>
        <td colspan="2">—</td>
        <td><strong>{total_netto:.1f}</strong></td>
        <td>Заявленный выход: {card.yield_.perBatch_g:.1f} г</td>
    </tr>
    """
    
    # Формируем процесс
    process_html = ""
    for step in card.process:
        time_str = f"{step.time_min:.0f}" if step.time_min else "—"
        temp_str = f"{step.temp_c:.0f}" if step.temp_c else "—"
        equipment_str = ", ".join(step.equipment) if step.equipment else "—"
        ccp_mark = "✓" if step.ccp else ""
        
        process_html += f"""
        <tr>
            <td>{step.n}</td>
            <td>{step.action}</td>
            <td>{time_str}</td>
            <td>{temp_str}</td>
            <td>{equipment_str}</td>
            <td>{ccp_mark}</td>
        </tr>
        """
    
    # Питательность
    nutrition_html = ""
    coverage_note = ""
    
    # Проверяем наличие nutritionMeta для определения покрытия
    coverage_pct = 0
    if hasattr(card, 'nutritionMeta') and card.nutritionMeta:
        coverage_pct = getattr(card.nutritionMeta, 'coveragePct', 0)
    
    if coverage_pct > 0 and card.nutrition:
        if card.nutrition.per100g:
            per100g = card.nutrition.per100g
            nutrition_html += f"""
            <tr>
                <td><strong>На 100г готового блюда</strong></td>
                <td>{round(per100g.kcal or 0):.0f}</td>
                <td>{(per100g.proteins_g or 0):.1f}</td>
                <td>{(per100g.fats_g or 0):.1f}</td>
                <td>{(per100g.carbs_g or 0):.1f}</td>
            </tr>
            """
        
        if card.nutrition.perPortion:
            perPortion = card.nutrition.perPortion
            nutrition_html += f"""
            <tr>
                <td><strong>На 1 порцию</strong></td>
                <td>{round(perPortion.kcal or 0):.0f}</td>
                <td>{(perPortion.proteins_g or 0):.1f}</td>
                <td>{(perPortion.fats_g or 0):.1f}</td>
                <td>{(perPortion.carbs_g or 0):.1f}</td>
            </tr>
            """
        
        # Добавляем примечание о покрытии если неполное
        if coverage_pct < 100:
            coverage_note = f'<tr><td colspan="5" style="font-style: italic; color: #666; font-size: 0.9em; text-align: center;">⚠️ Покрытие {coverage_pct}% (часть ингредиентов без данных)</td></tr>'
        else:
            coverage_note = f'<tr><td colspan="5" style="font-style: italic; color: #0a5d0a; font-size: 0.9em; text-align: center;">✅ Полные данные по всем ингредиентам</td></tr>'
    
    if not nutrition_html:
        nutrition_html = '<tr><td colspan="5"><em>Данные не заполнены</em></td></tr>'
    
    # Добавляем coverage_note к nutrition_html
    if coverage_note:
        nutrition_html += coverage_note
    
    # Формируем источник БЖУ для ГОСТ-печати
    nutrition_source_html = ""
    if hasattr(card, 'nutritionMeta') and card.nutritionMeta:
        source = getattr(card.nutritionMeta, 'source', 'не указан')
        asOf = getattr(card.nutritionMeta, 'asOf', '')
        
        if source == 'usda':
            source_display = 'USDA'
        elif source == 'catalog':
            source_display = 'каталог'
        elif source == 'bootstrap':
            source_display = 'демо-каталог'
        elif source == 'Mixed':
            source_display = 'Mixed'
        else:
            source_display = source
            
        nutrition_source_html = f'<p style="font-size: 0.9em; color: #666; text-align: center; margin-top: 8px;"><strong>Источник БЖУ:</strong> {source_display}'
        if asOf:
            nutrition_source_html += f'; дата: {asOf}'
        nutrition_source_html += '</p>'
    
    # Стоимость
    cost_html = ""
    if card.cost and card.cost.rawCost:
        cost_html = f"""
        <p><strong>Себестоимость:</strong> {card.cost.rawCost:.2f} ₽ (партия), {card.cost.costPerPortion:.2f} ₽ (порция)</p>
        <p><strong>Наценка:</strong> {card.cost.markup_pct:.0f}%, НДС: {card.cost.vat_pct:.0f}%</p>
        """
    else:
        cost_html = '<p><em>Данные о стоимости не заполнены</em></p>'
    
    # Issues
    issues_html = ""
    if issues:
        issues_html = '<div class="issues"><h4>Замечания:</h4><ul>'
        for issue in issues:
            issues_html += f'<li>{issue}</li>'
        issues_html += '</ul></div>'
    
    # QR код с ID
    qr_text = f"TechCard ID: {card.meta.id}"
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Техкарта - {card.meta.title}</title>
    <style>
        @page {{ size: A4; margin: 15mm; }}
        @media print {{
            body {{ -webkit-print-color-adjust: exact; }}
            .no-print {{ display: none; }}
            .page-break {{ page-break-before: always; }}
            table {{ page-break-inside: avoid; }}
            tr {{ page-break-inside: avoid; }}
        }}
        
        body {{ font-family: Arial, sans-serif; font-size: 11pt; line-height: 1.3; margin: 0; position: relative; }}
        
        .watermark {{
            position: fixed; top: 50%; left: 50%;
            transform: translate(-50%, -50%) rotate(-45deg);
            font-size: 72pt; font-weight: bold; color: rgba(255,0,0,0.1);
            z-index: -1; pointer-events: none;
        }}
        
        .header {{ text-align: center; margin-bottom: 20px; border-bottom: 2px solid #000; padding-bottom: 10px; }}
        .title {{ font-size: 16pt; font-weight: bold; margin-bottom: 5px; }}
        .meta-info {{ font-size: 10pt; margin-bottom: 15px; }}
        
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
        th, td {{ border: 1px solid #333; padding: 6px 8px; text-align: left; font-size: 10pt; }}
        th {{ background-color: #f0f0f0; font-weight: bold; text-align: center; }}
        .total-row {{ background-color: #f8f8f8; font-weight: bold; }}
        
        .section {{ margin-bottom: 20px; }}
        .section h3 {{ font-size: 12pt; font-weight: bold; margin-bottom: 8px; border-bottom: 1px solid #666; padding-bottom: 3px; }}
        
        .storage {{ background-color: #f9f9f9; padding: 8px; border: 1px solid #ccc; margin-bottom: 15px; }}
        .issues {{ background-color: #ffe6e6; padding: 10px; border: 1px solid #ff0000; margin-bottom: 15px; }}
        
        .footer {{ position: fixed; bottom: 0; width: 100%; text-align: center; font-size: 9pt; border-top: 1px solid #666; padding-top: 5px; }}
    </style>
</head>
<body>
    {watermark_html}
    
    <div class="header">
        <div class="title">ТЕХНОЛОГИЧЕСКАЯ КАРТА</div>
        <div class="title">{card.meta.title}</div>
        <div class="meta-info">
            Версия: {card.meta.version} | Дата: {card.meta.createdAt.strftime('%d.%m.%Y') if isinstance(card.meta.createdAt, datetime) else 'не указана'} | 
            Кухня: {card.meta.cuisine or 'не указана'} | 
            Порций: {card.portions} | Выход на порцию: {card.yield_.perPortion_g:.0f}г | Выход партии: {card.yield_.perBatch_g:.0f}г
        </div>
    </div>
    
    {issues_html}
    
    <div class="section">
        <h3>СОСТАВ И РАСХОД СЫРЬЯ</h3>
        <table>
            <thead>
                <tr>
                    <th>Наименование</th>
                    <th>Брутто, г</th>
                    <th>Потери, %</th>
                    <th>Нетто, г</th>
                    <th>Ед.</th>
                </tr>
            </thead>
            <tbody>
                {ingredients_html}
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <h3>ТЕХНОЛОГИЧЕСКИЙ ПРОЦЕСС</h3>
        <table>
            <thead>
                <tr>
                    <th>№</th>
                    <th>Действие</th>
                    <th>Время, мин</th>
                    <th>Темп., °C</th>
                    <th>Оборудование</th>
                    <th>CCP</th>
                </tr>
            </thead>
            <tbody>
                {process_html}
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <h3>УСЛОВИЯ И СРОКИ ХРАНЕНИЯ</h3>
        <div class="storage">
            <p><strong>Условия:</strong> {card.storage.conditions}</p>
            <p><strong>Срок хранения:</strong> {card.storage.shelfLife_hours:.0f} часов</p>
            <p><strong>Температура подачи:</strong> {card.storage.servingTemp_c or 'не указана'}°C</p>
        </div>
    </div>
    
    <div class="section">
        <h3>ПИЩЕВАЯ ЦЕННОСТЬ</h3>
        <table>
            <thead>
                <tr>
                    <th>Показатель</th>
                    <th>ккал</th>
                    <th>Белки, г</th>
                    <th>Жиры, г</th>
                    <th>Углеводы, г</th>
                </tr>
            </thead>
            <tbody>
                {nutrition_html}
            </tbody>
        </table>
        {nutrition_source_html}
    </div>
    
    <div class="section">
        <h3>ЭКОНОМИЧЕСКИЕ ПОКАЗАТЕЛИ</h3>
        {cost_html}
    </div>
    
    <div style="margin-top: 30px;">
        <p><strong>Примечания:</strong> {'; '.join(card.printNotes) if card.printNotes else 'отсутствуют'}</p>
        <br>
        <table style="width: 100%; border: none;">
            <tr style="border: none;">
                <td style="border: none; width: 50%;">Ответственный: ________________</td>
                <td style="border: none; width: 50%;">Утверждено: ________________</td>
            </tr>
        </table>
    </div>
    
    <div class="footer">
        Стр. 1 | Дата печати: {datetime.now().strftime('%d.%m.%Y %H:%M')} | {qr_text}
    </div>
</body>
</html>"""
    
    return html_content