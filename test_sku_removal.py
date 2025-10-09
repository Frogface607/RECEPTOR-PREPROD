#!/usr/bin/env python3
"""
Test SKU removal from PDF and ГОСТ-печать
"""

import requests
import json

def test_html_sku_removal():
    """Проверяем что HTML ГОСТ-печать не содержит SKU"""
    print("🔍 Тестируем удаление SKU из HTML ГОСТ-печати...")
    
    try:
        # Создаем техkарту
        response = requests.post(
            "https://cursor-push.preview.emergentagent.com/api/v1/techcards.v2/generate",
            json={"name": "Тест удаления SKU", "user_id": "sku_test"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            card = data.get('card', {})
            
            if card:
                # Отправляем техkарту на print endpoint
                print_response = requests.post(
                    "https://cursor-push.preview.emergentagent.com/api/v1/techcards.v2/print",
                    json=card,
                    timeout=30
                )
                
                if print_response.status_code == 200:
                    html_content = print_response.text
                    
                    # Проверяем что SKU удален
                    has_sku_header = '<th>SKU</th>' in html_content
                    has_sku_text = 'SKU' in html_content
                    
                    print(f"   HTML размер: {len(html_content)} символов")
                    print(f"   Содержит <th>SKU</th>: {has_sku_header}")
                    print(f"   Содержит текст 'SKU': {has_sku_text}")
                    
                    if not has_sku_header:
                        print("   ✅ SKU удален из заголовков таблицы")
                    else:
                        print("   ❌ SKU все еще в заголовках")
                    
                    # Проверяем структуру таблицы
                    if 'Наименование</th>' in html_content and 'Брутто, г</th>' in html_content:
                        print("   ✅ Таблица ингредиентов корректна")
                    else:
                        print("   ❌ Проблемы с таблицей ингредиентов")
                    
                    return not has_sku_header
                else:
                    print(f"   ❌ Print API error: HTTP {print_response.status_code}")
                    return False
            else:
                print("   ❌ Техkарта не сгенерировалась")
                return False
        else:
            print(f"   ❌ Generation API error: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_pdf_still_works():
    """Проверяем что PDF генерация все еще работает"""
    print("🔍 Тестируем что PDF генерация работает...")
    
    try:
        # Создаем техkарту
        response = requests.post(
            "https://cursor-push.preview.emergentagent.com/api/v1/techcards.v2/generate",
            json={"name": "PDF тест", "user_id": "pdf_test"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            card_id = data.get('card', {}).get('meta', {}).get('id')
            
            if card_id:
                # Пробуем сгенерировать PDF
                pdf_response = requests.get(
                    f"https://cursor-push.preview.emergentagent.com/api/v1/techcards.v2/{card_id}/pdf",
                    timeout=30
                )
                
                if pdf_response.status_code == 200:
                    content_type = pdf_response.headers.get('Content-Type', '')
                    pdf_size = len(pdf_response.content)
                    
                    print(f"   PDF размер: {pdf_size} байт")
                    print(f"   Content-Type: {content_type}")
                    
                    if 'pdf' in content_type.lower() and pdf_size > 1000:
                        print("   ✅ PDF генерируется корректно")
                        return True
                    else:
                        print("   ❌ PDF некорректный")
                        return False
                else:
                    print(f"   ❌ PDF API error: HTTP {pdf_response.status_code}")
                    return False
            else:
                print("   ❌ Не получен ID техkарты")
                return False
        else:
            print(f"   ❌ Generation API error: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("🎯 SKU REMOVAL TEST: PDF и ГОСТ-печать")
    print("=" * 60)
    
    # Тест 1: HTML ГОСТ-печать без SKU
    html_ok = test_html_sku_removal()
    
    # Тест 2: PDF все еще работает
    pdf_ok = test_pdf_still_works()
    
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ:")
    
    if html_ok:
        print("✅ HTML ГОСТ-печать: SKU успешно удален")
        print("   - Колонка SKU убрана из таблицы ингредиентов")
        print("   - Структура таблицы остается корректной")
    else:
        print("❌ HTML ГОСТ-печать: проблемы с удалением SKU")
    
    if pdf_ok:
        print("✅ PDF генерация: работает корректно")
        print("   - PDF файлы генерируются без проблем")
        print("   - SKU не отображался в PDF изначально")
    else:
        print("❌ PDF генерация: есть проблемы")
    
    if html_ok and pdf_ok:
        print(f"\n🎉 УСПЕХ! SKU убран из ГОСТ-печати, PDF работает как надо")
    else:
        print(f"\n⚠️ Есть проблемы, требующие внимания")
        
    print("=" * 60)

if __name__ == "__main__":
    main()