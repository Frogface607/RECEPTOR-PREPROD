from __future__ import annotations
from receptor_agent.techcards_v2.schemas import TechCardV2

def generate_print_html(card: TechCardV2, status: str = "success", issues: list = None) -> str:
    """Генерация HTML для печати техкарты с водяным знаком статуса"""
    if issues is None:
        issues = []
    
    # Определяем стиль водяного знака
    watermark_style = ""
    watermark_text = ""
    
    if status == "draft":
        watermark_style = "color: rgba(255, 0, 0, 0.3); font-size: 120px; transform: rotate(-45deg);"
        watermark_text = "ЧЕРНОВИК"
    elif status == "success":
        watermark_style = "color: rgba(0, 128, 0, 0.2); font-size: 100px; transform: rotate(-45deg);"
        watermark_text = "УТВЕРЖДЕНО"
    
    # Формируем список ингредиентов
    ingredients_html = ""
    for ing in card.ingredients:
        ingredients_html += f"""
        <tr>
            <td>{ing.canonical or ing.name}</td>
            <td>{ing.gross_g:.1f} г</td>
            <td>{ing.net_g:.1f} г</td>
            <td>{ing.loss_pct:.1f}%</td>
        </tr>
        """
    
    # Формируем процесс приготовления
    process_html = ""
    for step in card.process:
        time_info = f" (~{step.time_min} мин)" if step.time_min else ""
        temp_info = f" ({step.temp_c}°C)" if step.temp_c else ""
        process_html += f"""
        <div class="process-step">
            <strong>{step.step}.</strong> {step.desc}{time_info}{temp_info}
        </div>
        """
    
    # Формируем HACCP
    haccp_html = ""
    for ccp in card.haccp.ccp:
        haccp_html += f"""
        <div class="haccp-item">
            <strong>{ccp.name}:</strong> лимит {ccp.limit}; мониторинг: {ccp.monitoring}; корректирующие: {ccp.corrective}
        </div>
        """
    
    # Формируем список проблем (если есть)
    issues_html = ""
    if issues:
        issues_html = """
        <div class="issues-section">
            <h3 style="color: red;">Обнаруженные проблемы:</h3>
            <ul>
        """
        for issue in issues:
            issues_html += f"<li>{issue}</li>"
        issues_html += "</ul></div>"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Техкарта: {card.meta.name}</title>
        <style>
            @page {{ size: A4; margin: 2cm; }}
            body {{ font-family: Arial, sans-serif; font-size: 12px; line-height: 1.4; position: relative; }}
            .header {{ text-align: center; margin-bottom: 20px; }}
            .title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
            .meta {{ margin-bottom: 15px; }}
            .section {{ margin-bottom: 20px; }}
            .section h3 {{ font-size: 14px; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid #ccc; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
            th {{ background-color: #f5f5f5; font-weight: bold; }}
            .process-step {{ margin-bottom: 8px; }}
            .haccp-item {{ margin-bottom: 8px; }}
            .watermark {{
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(-45deg);
                font-weight: bold;
                z-index: -1;
                pointer-events: none;
                {watermark_style}
            }}
            .issues-section {{ 
                background-color: #ffe6e6; 
                border: 2px solid #ff0000; 
                padding: 15px; 
                margin: 20px 0; 
                border-radius: 5px; 
            }}
            @media print {{
                .issues-section {{ 
                    background-color: #f0f0f0 !important; 
                    -webkit-print-color-adjust: exact; 
                }}
            }}
        </style>
    </head>
    <body>
        <div class="watermark">{watermark_text}</div>
        
        <div class="header">
            <div class="title">ТЕХНОЛОГИЧЕСКАЯ КАРТА</div>
            <div class="title">{card.meta.name}</div>
        </div>
        
        <div class="meta">
            <strong>Категория:</strong> {card.meta.category or 'Не указана'}<br>
            <strong>Кухня:</strong> {card.meta.cuisine or 'Не указана'}<br>
            <strong>Выход:</strong> {card.yield_.portions} порций × {card.yield_.per_portion_g} г = {card.yield_.total_net_g} г
        </div>
        
        {issues_html}
        
        <div class="section">
            <h3>СОСТАВ И РАСХОД СЫРЬЯ</h3>
            <table>
                <thead>
                    <tr>
                        <th>Наименование сырья</th>
                        <th>Масса брутто, г</th>
                        <th>Масса нетто, г</th>
                        <th>Потери, %</th>
                    </tr>
                </thead>
                <tbody>
                    {ingredients_html}
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h3>ТЕХНОЛОГИЯ ПРИГОТОВЛЕНИЯ</h3>
            {process_html}
        </div>
        
        <div class="section">
            <h3>КОНТРОЛЬНЫЕ КРИТИЧЕСКИЕ ТОЧКИ (HACCP)</h3>
            {haccp_html}
        </div>
        
        <div style="margin-top: 40px; text-align: right; font-size: 10px;">
            Статус: {status.upper()}
        </div>
    </body>
    </html>
    """
    
    return html_content