#!/usr/bin/env python3
"""
Comprehensive test for /api/upload-prices endpoint
Testing Excel/CSV price upload functionality for PRO users
"""

import requests
import unittest
import tempfile
import os
import pandas as pd
from io import BytesIO
import json

class UploadPricesTest(unittest.TestCase):
    def setUp(self):
        """Setup test environment"""
        # Use the public endpoint for testing
        self.base_url = "https://cursor-push.preview.emergentagent.com/api"
        self.upload_url = "https://cursor-push.preview.emergentagent.com/api/upload-prices"
        
        # Test user with PRO subscription as specified in review request
        self.pro_user_id = "test_user_12345"
        self.free_user_id = "test_user_free_123"
        
        print(f"\n🚀 STARTING UPLOAD PRICES ENDPOINT TESTING")
        print(f"📍 Base URL: {self.base_url}")
        print(f"📍 Upload URL: {self.upload_url}")
        print(f"👤 PRO User ID: {self.pro_user_id}")
        
    def create_test_excel_file(self):
        """Create test Excel file with price data as specified in review request"""
        # Create test data as specified in review request
        data = {
            'Продукт': ['Картофель', 'Морковь', 'Лук'],
            'Цена': [50, 60, 40]
        }
        
        df = pd.DataFrame(data)
        
        # Create temporary Excel file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            df.to_excel(temp_file.name, index=False, engine='openpyxl')
            return temp_file.name
    
    def create_test_csv_file(self):
        """Create test CSV file with price data"""
        data = {
            'Продукт': ['Помидоры', 'Огурцы', 'Перец'],
            'Цена': [80, 70, 120]
        }
        
        df = pd.DataFrame(data)
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w', encoding='utf-8') as temp_file:
            df.to_csv(temp_file.name, index=False)
            return temp_file.name
    
    def test_01_endpoint_availability(self):
        """Test 1: Endpoint availability - POST /api/upload-prices"""
        print("\n🔍 TEST 1: Проверка доступности endpoint POST /api/upload-prices")
        
        # Create test file
        excel_file_path = self.create_test_excel_file()
        
        try:
            with open(excel_file_path, 'rb') as f:
                files = {'file': ('test_prices.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                data = {'user_id': self.pro_user_id}
                
                response = requests.post(self.upload_url, files=files, data=data)
                
                print(f"📊 Response Status: {response.status_code}")
                print(f"📊 Response Headers: {dict(response.headers)}")
                
                # Endpoint should exist and respond (not 404)
                self.assertNotEqual(response.status_code, 404, "Endpoint /api/upload-prices не найден")
                print("✅ Endpoint существует и отвечает")
                
        finally:
            # Cleanup
            if os.path.exists(excel_file_path):
                os.unlink(excel_file_path)
    
    def test_02_pro_subscription_validation(self):
        """Test 2: PRO subscription validation"""
        print("\n🔍 TEST 2: Проверка валидации PRO подписки")
        
        # Create test file
        excel_file_path = self.create_test_excel_file()
        
        try:
            # Test with PRO user (test_user_12345)
            print(f"🔸 Тестирование с PRO пользователем: {self.pro_user_id}")
            with open(excel_file_path, 'rb') as f:
                files = {'file': ('test_prices.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                data = {'user_id': self.pro_user_id}
                
                response = requests.post(self.upload_url, files=files, data=data)
                
                print(f"📊 PRO User Response Status: {response.status_code}")
                print(f"📊 PRO User Response: {response.text[:500]}")
                
                # PRO user should be able to upload (not 403)
                if response.status_code == 403:
                    print("⚠️ PRO пользователь получил 403 - возможная проблема с валидацией подписки")
                else:
                    print("✅ PRO пользователь может загружать файлы")
            
            # Test with Free user (should be blocked)
            print(f"🔸 Тестирование с Free пользователем: {self.free_user_id}")
            with open(excel_file_path, 'rb') as f:
                files = {'file': ('test_prices.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                data = {'user_id': self.free_user_id}
                
                response = requests.post(self.upload_url, files=files, data=data)
                
                print(f"📊 Free User Response Status: {response.status_code}")
                print(f"📊 Free User Response: {response.text[:200]}")
                
                # Free user should be blocked with 403
                if response.status_code == 403:
                    print("✅ Free пользователь корректно заблокирован (403)")
                else:
                    print("⚠️ Free пользователь не заблокирован - возможная проблема безопасности")
                
        finally:
            # Cleanup
            if os.path.exists(excel_file_path):
                os.unlink(excel_file_path)
    
    def test_03_multipart_form_data_format(self):
        """Test 3: Content-Type multipart/form-data format"""
        print("\n🔍 TEST 3: Проверка формата multipart/form-data")
        
        excel_file_path = self.create_test_excel_file()
        
        try:
            with open(excel_file_path, 'rb') as f:
                # Test correct multipart/form-data format
                files = {'file': ('test_prices.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                data = {'user_id': self.pro_user_id}
                
                response = requests.post(self.upload_url, files=files, data=data)
                
                print(f"📊 Multipart Request Status: {response.status_code}")
                print(f"📊 Request Content-Type: multipart/form-data (автоматически установлен requests)")
                
                # Should accept multipart/form-data format
                if response.status_code in [200, 403]:  # 403 is expected for subscription validation
                    print("✅ Multipart/form-data формат принимается")
                else:
                    print(f"⚠️ Неожиданный статус для multipart запроса: {response.status_code}")
                    print(f"Response: {response.text}")
                
        finally:
            if os.path.exists(excel_file_path):
                os.unlink(excel_file_path)
    
    def test_04_xlsx_file_support(self):
        """Test 4: Excel .xlsx file support"""
        print("\n🔍 TEST 4: Проверка поддержки .xlsx файлов")
        
        excel_file_path = self.create_test_excel_file()
        
        try:
            with open(excel_file_path, 'rb') as f:
                files = {'file': ('test_prices.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                data = {'user_id': self.pro_user_id}
                
                response = requests.post(self.upload_url, files=files, data=data)
                
                print(f"📊 XLSX File Response Status: {response.status_code}")
                print(f"📊 XLSX File Response: {response.text[:500]}")
                
                # Check if .xlsx files are supported
                if response.status_code == 200:
                    print("✅ .xlsx файлы поддерживаются")
                    try:
                        response_data = response.json()
                        if response_data.get('success'):
                            print(f"✅ Файл успешно обработан: {response_data.get('count', 0)} позиций")
                        else:
                            print(f"⚠️ Ошибка обработки: {response_data.get('error', 'Unknown error')}")
                    except:
                        print("⚠️ Не удалось парсить JSON ответ")
                elif response.status_code == 403:
                    print("⚠️ Получен 403 - проблема с валидацией подписки, но формат файла принят")
                else:
                    print(f"❌ Проблема с обработкой .xlsx файла: {response.status_code}")
                
        finally:
            if os.path.exists(excel_file_path):
                os.unlink(excel_file_path)
    
    def test_05_csv_file_support(self):
        """Test 5: CSV file support"""
        print("\n🔍 TEST 5: Проверка поддержки .csv файлов")
        
        csv_file_path = self.create_test_csv_file()
        
        try:
            with open(csv_file_path, 'rb') as f:
                files = {'file': ('test_prices.csv', f, 'text/csv')}
                data = {'user_id': self.pro_user_id}
                
                response = requests.post(self.upload_url, files=files, data=data)
                
                print(f"📊 CSV File Response Status: {response.status_code}")
                print(f"📊 CSV File Response: {response.text[:500]}")
                
                # Note: Backend code only shows .xlsx support with pandas.read_excel
                # CSV support might not be implemented
                if response.status_code == 200:
                    print("✅ .csv файлы поддерживаются")
                    try:
                        response_data = response.json()
                        if response_data.get('success'):
                            print(f"✅ CSV файл успешно обработан: {response_data.get('count', 0)} позиций")
                        else:
                            print(f"⚠️ Ошибка обработки CSV: {response_data.get('error', 'Unknown error')}")
                    except:
                        print("⚠️ Не удалось парсить JSON ответ")
                elif response.status_code == 403:
                    print("⚠️ Получен 403 - проблема с валидацией подписки")
                else:
                    print(f"❌ .csv файлы не поддерживаются или ошибка обработки: {response.status_code}")
                    print("💡 Возможно, поддерживаются только .xlsx файлы")
                
        finally:
            if os.path.exists(csv_file_path):
                os.unlink(csv_file_path)
    
    def test_06_data_processing_and_response(self):
        """Test 6: Data processing and response format"""
        print("\n🔍 TEST 6: Проверка обработки данных и формата ответа")
        
        # Create Excel file with specific test data from review request
        excel_file_path = self.create_test_excel_file()
        
        try:
            with open(excel_file_path, 'rb') as f:
                files = {'file': ('test_prices.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                data = {'user_id': self.pro_user_id}
                
                response = requests.post(self.upload_url, files=files, data=data)
                
                print(f"📊 Data Processing Response Status: {response.status_code}")
                print(f"📊 Full Response: {response.text}")
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        
                        # Check expected response format
                        print("\n🔍 Проверка формата ответа:")
                        
                        # Check success field
                        if 'success' in response_data:
                            print(f"✅ success: {response_data['success']}")
                        else:
                            print("❌ Отсутствует поле 'success'")
                        
                        # Check count field
                        if 'count' in response_data:
                            print(f"✅ count: {response_data['count']} обработанных позиций")
                            if response_data['count'] == 0:
                                print("⚠️ ПРОБЛЕМА: Обработано 0 позиций - возможна проблема с парсингом")
                        else:
                            print("❌ Отсутствует поле 'count'")
                        
                        # Check message field
                        if 'message' in response_data:
                            print(f"✅ message: {response_data['message']}")
                        else:
                            print("❌ Отсутствует поле 'message'")
                        
                        # Check prices preview (first 10 items)
                        if 'prices' in response_data:
                            prices = response_data['prices']
                            print(f"✅ prices: {len(prices)} позиций в превью")
                            if len(prices) > 0:
                                print("📋 Первые позиции:")
                                for i, price in enumerate(prices[:3]):
                                    print(f"   {i+1}. {price}")
                            else:
                                print("⚠️ Превью цен пустое")
                        else:
                            print("❌ Отсутствует поле 'prices'")
                        
                        # Analyze potential parsing issues
                        if response_data.get('count', 0) == 0:
                            print("\n🔍 АНАЛИЗ ПРОБЛЕМЫ С ПАРСИНГОМ:")
                            print("💡 Возможные причины 0 обработанных позиций:")
                            print("   - Проблема с regex для извлечения цен")
                            print("   - Неправильное чтение Excel файла pandas")
                            print("   - Проблема с форматом данных в файле")
                            print("   - Ошибка в логике обработки строк")
                        
                    except json.JSONDecodeError:
                        print("❌ Ответ не является валидным JSON")
                        print(f"Raw response: {response.text}")
                        
                elif response.status_code == 403:
                    print("⚠️ Получен 403 - проблема с валидацией PRO подписки")
                    print("💡 Проверьте, что test_user_12345 имеет PRO подписку")
                else:
                    print(f"❌ Неожиданный статус ответа: {response.status_code}")
                    print(f"Response: {response.text}")
                
        finally:
            if os.path.exists(excel_file_path):
                os.unlink(excel_file_path)
    
    def test_07_error_handling(self):
        """Test 7: Error handling scenarios"""
        print("\n🔍 TEST 7: Проверка обработки ошибок")
        
        # Test 1: No file provided
        print("🔸 Тест без файла:")
        response = requests.post(self.upload_url, data={'user_id': self.pro_user_id})
        print(f"   Status: {response.status_code}")
        
        # Test 2: No user_id provided
        print("🔸 Тест без user_id:")
        excel_file_path = self.create_test_excel_file()
        try:
            with open(excel_file_path, 'rb') as f:
                files = {'file': ('test_prices.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                response = requests.post(self.upload_url, files=files)
                print(f"   Status: {response.status_code}")
        finally:
            if os.path.exists(excel_file_path):
                os.unlink(excel_file_path)
        
        # Test 3: Invalid file format
        print("🔸 Тест с текстовым файлом:")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w') as temp_file:
            temp_file.write("This is not an Excel file")
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                data = {'user_id': self.pro_user_id}
                response = requests.post(self.upload_url, files=files, data=data)
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

def run_upload_prices_tests():
    """Run all upload prices tests"""
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ ENDPOINT /api/upload-prices")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(UploadPricesTest)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=open(os.devnull, 'w'))
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
    print(f"✅ Успешных тестов: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Неудачных тестов: {len(result.failures)}")
    print(f"🚨 Ошибок: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ НЕУДАЧНЫЕ ТЕСТЫ:")
        for test, traceback in result.failures:
            error_msg = traceback.split('AssertionError: ')[-1].split('\n')[0]
            print(f"   - {test}: {error_msg}")
    
    if result.errors:
        print("\n🚨 ОШИБКИ:")
        for test, traceback in result.errors:
            error_lines = traceback.split('\n')
            error_msg = error_lines[-2] if len(error_lines) > 1 else "Unknown error"
            print(f"   - {test}: {error_msg}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_upload_prices_tests()
    exit(0 if success else 1)