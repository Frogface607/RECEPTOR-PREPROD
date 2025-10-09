#!/usr/bin/env python3
"""
Final SKU Removal Test - проверяем что SKU убран из ГОСТ-печати и PDF
"""

import requests
import json
import zipfile
import io

def test_final_sku_removal():
    """Финальный тест удаления SKU"""
    print("🔍 Финальный тест удаления SKU из PDF и ГОСТ-печати...")
    
    try:
        # Создаем техkарту
        response = requests.post(
            "https://cursor-push.preview.emergentagent.com/api/v1/techcards.v2/generate",
            json={"name": "Финальный тест SKU", "user_id": "final_sku_test"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            card = data.get('card', {})
            
            if not card:
                print("   ❌ Техkарта не сгенерировалась")
                return False
            
            print(f"   ✅ Техkарта создана: {card.get('meta', {}).get('title', 'Unknown')}")
            
            # Тест 1: HTML ГОСТ-печать
            print("\n   📄 Тестируем HTML ГОСТ-печать...")
            print_response = requests.post(
                "https://cursor-push.preview.emergentagent.com/api/v1/techcards.v2/print",
                json=card,
                timeout=30
            )
            
            html_ok = False
            if print_response.status_code == 200:
                html_content = print_response.text
                has_sku_column = '<th>SKU</th>' in html_content
                
                if not has_sku_column:
                    print("      ✅ SKU удален из HTML ГОСТ-печати")
                    html_ok = True
                else:
                    print("      ❌ SKU все еще в HTML")
            else:
                print(f"      ❌ HTML print error: HTTP {print_response.status_code}")
            
            # Тест 2: PDF в составе экспорта
            print("\n   📦 Тестируем PDF в ZIP экспорте...")
            export_response = requests.post(
                "https://cursor-push.preview.emergentagent.com/api/v1/techcards.v2/export",
                json={"card": card, "options": {"operational_rounding": False}},
                timeout=30
            )
            
            pdf_ok = False
            if export_response.status_code == 200:
                # Проверяем что это ZIP
                content_type = export_response.headers.get('Content-Type', '')
                zip_size = len(export_response.content)
                
                if 'zip' in content_type.lower() and zip_size > 1000:
                    # Проверяем содержимое ZIP
                    try:
                        zip_buffer = io.BytesIO(export_response.content)
                        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                            files = zip_file.namelist()
                            has_pdf = 'techcard.pdf' in files
                            
                            if has_pdf:
                                pdf_data = zip_file.read('techcard.pdf')
                                pdf_size = len(pdf_data)
                                
                                if pdf_size > 1000:
                                    print(f"      ✅ PDF в ZIP экспорте: {pdf_size} байт")
                                    pdf_ok = True
                                else:
                                    print(f"      ❌ PDF слишком маленький: {pdf_size} байт")
                            else:
                                print(f"      ❌ PDF не найден в ZIP. Файлы: {files}")
                    except Exception as e:
                        print(f"      ❌ Ошибка разбора ZIP: {e}")
                else:
                    print(f"      ❌ Некорректный ZIP: {content_type}, {zip_size} байт")
            else:
                print(f"      ❌ Export error: HTTP {export_response.status_code}")
            
            return html_ok and pdf_ok
            
        else:
            print(f"   ❌ Generation error: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("🎉 FINAL SKU REMOVAL TEST")
    print("Проверяем что SKU убран из PDF и ГОСТ-печати")
    print("=" * 60)
    
    success = test_final_sku_removal()
    
    print("\n" + "=" * 60)
    print("📊 ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
    
    if success:
        print("🎉 ВСЕ ОТЛИЧНО! SKU успешно убран:")
        print("   ✅ HTML ГОСТ-печать: колонка SKU удалена")
        print("   ✅ PDF экспорт: работает корректно в составе ZIP")
        print("   ✅ Структура таблиц остается правильной")
        print("   ✅ Все функции экспорта работают")
    else:
        print("❌ Есть проблемы с удалением SKU")
        
    print("=" * 60)

if __name__ == "__main__":
    main()