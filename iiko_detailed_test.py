#!/usr/bin/env python3
"""
Detailed IIKo Authentication Diagnostic Test
Testing the exact authentication flow with detailed logging
"""

import requests
import json
import time
import sys
from datetime import datetime
import httpx
import asyncio

# Get backend URL from environment
BACKEND_URL = "https://kitchen-pro-2.preview.emergentagent.com/api"

# IIKo credentials from user
IIKO_LOGIN = "Sergey"
IIKO_PASSWORD = "metkamfetamin"
IIKO_BASE_URL = "https://edison-bar.iiko.it"

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"[{timestamp}] {status_emoji} {test_name}: {status}")
    if details:
        print(f"    Details: {details}")
    print()

async def test_direct_iiko_auth():
    """Test direct authentication with IIKo Office API"""
    print("🔐 DIRECT IIKO OFFICE AUTHENTICATION TEST")
    print("=" * 60)
    
    print(f"Testing direct auth to: {IIKO_BASE_URL}/resto/api/auth")
    print(f"Login: {IIKO_LOGIN}")
    print(f"Password: {'*' * len(IIKO_PASSWORD)}")
    print()
    
    try:
        auth_url = f"{IIKO_BASE_URL}/resto/api/auth"
        
        payload = {
            "login": IIKO_LOGIN,
            "pass": IIKO_PASSWORD
        }
        
        print(f"Making request to: {auth_url}")
        print(f"Payload: login={IIKO_LOGIN}, pass={'*' * len(IIKO_PASSWORD)}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(auth_url, params=payload)
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Text: {response.text}")
            
            if response.status_code == 200:
                session_key = response.text.strip()
                if session_key:
                    log_test("🎉 DIRECT AUTH SUCCESS", "PASS", 
                            f"Session key obtained: {session_key[:20]}...")
                    return session_key
                else:
                    log_test("Empty session key", "FAIL", "Response was 200 but no session key")
            elif response.status_code == 401:
                log_test("❌ AUTHENTICATION FAILED", "FAIL", 
                        f"401 Unauthorized: {response.text}")
                
                # Try to parse the error message
                error_text = response.text
                if "Неверный пароль" in error_text:
                    print("    🔍 ANALYSIS: Password is incorrect for this user")
                elif "пользователь" in error_text:
                    print("    🔍 ANALYSIS: User account issue")
                else:
                    print(f"    🔍 ANALYSIS: Unknown auth error: {error_text}")
            else:
                log_test("Unexpected response", "FAIL", 
                        f"HTTP {response.status_code}: {response.text}")
                
    except Exception as e:
        log_test("Direct auth test", "FAIL", f"Exception: {str(e)}")
    
    return None

async def test_alternative_auth_methods():
    """Test alternative authentication methods"""
    print("🔄 TESTING ALTERNATIVE AUTH METHODS")
    print("=" * 60)
    
    # Test 1: POST instead of GET
    print("Test 1: POST method instead of GET")
    try:
        auth_url = f"{IIKO_BASE_URL}/resto/api/auth"
        
        payload = {
            "login": IIKO_LOGIN,
            "pass": IIKO_PASSWORD
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(auth_url, json=payload)
            
            print(f"POST Response Status: {response.status_code}")
            print(f"POST Response Text: {response.text}")
            
            if response.status_code == 200:
                log_test("POST auth method", "PASS", "POST method works")
            else:
                log_test("POST auth method", "INFO", f"POST failed: {response.status_code}")
                
    except Exception as e:
        log_test("POST auth method", "FAIL", f"Exception: {str(e)}")
    
    # Test 2: Different parameter names
    print("Test 2: Alternative parameter names")
    try:
        auth_url = f"{IIKO_BASE_URL}/resto/api/auth"
        
        # Try different parameter combinations
        param_combinations = [
            {"username": IIKO_LOGIN, "password": IIKO_PASSWORD},
            {"user": IIKO_LOGIN, "pwd": IIKO_PASSWORD},
            {"login": IIKO_LOGIN, "password": IIKO_PASSWORD},
        ]
        
        for i, params in enumerate(param_combinations):
            print(f"  Trying combination {i+1}: {list(params.keys())}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(auth_url, params=params)
                
                print(f"    Status: {response.status_code}, Response: {response.text[:100]}")
                
                if response.status_code == 200:
                    log_test(f"Alt params {i+1}", "PASS", f"Works with {list(params.keys())}")
                    break
                    
    except Exception as e:
        log_test("Alternative parameters", "FAIL", f"Exception: {str(e)}")

def test_backend_diagnostics():
    """Test backend diagnostics for more details"""
    print("🔧 BACKEND DIAGNOSTICS")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/diagnostics", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print("Full diagnostic data:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Look for specific error details
            diagnosis = result.get('diagnosis', {})
            tests = diagnosis.get('tests', [])
            
            for test in tests:
                if test.get('test_name') == 'Authentication':
                    print(f"\n🔍 Authentication Test Details:")
                    print(f"Status: {test.get('status')}")
                    print(f"Issues: {test.get('issues', [])}")
                    
        else:
            log_test("Backend diagnostics", "FAIL", f"HTTP {response.status_code}")
            
    except Exception as e:
        log_test("Backend diagnostics", "FAIL", f"Exception: {str(e)}")

async def main():
    """Run detailed IIKo authentication diagnostics"""
    print("🔍 DETAILED IIKO AUTHENTICATION DIAGNOSTIC")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("🎯 ЦЕЛЬ: Выяснить точную причину ошибки аутентификации")
    print("📋 ИЗВЕСТНАЯ ПРОБЛЕМА: '401 Неверный пароль для пользователя Орлов Сергей Артемович'")
    print()
    print("🔑 ТЕСТИРУЕМЫЕ КРЕДЫ:")
    print(f"- Login: {IIKO_LOGIN}")
    print(f"- Password: {'*' * len(IIKO_PASSWORD)}")
    print(f"- Server: {IIKO_BASE_URL}")
    print()
    
    try:
        # Test 1: Direct authentication
        session_key = await test_direct_iiko_auth()
        
        if not session_key:
            # Test 2: Alternative methods
            await test_alternative_auth_methods()
        
        # Test 3: Backend diagnostics
        test_backend_diagnostics()
        
        print("🏁 ДИАГНОСТИКА ЗАВЕРШЕНА")
        print("=" * 80)
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        if session_key:
            print("✅ РЕЗУЛЬТАТ: Аутентификация успешна!")
            print(f"Session key: {session_key[:20]}...")
        else:
            print("❌ РЕЗУЛЬТАТ: Аутентификация не удалась")
            print()
            print("🔍 ВОЗМОЖНЫЕ ПРИЧИНЫ:")
            print("1. Неверный пароль (наиболее вероятно)")
            print("2. Аккаунт заблокирован или деактивирован")
            print("3. Требуется другой метод аутентификации")
            print("4. Проблемы с кодировкой символов в пароле")
            print("5. Сервер требует дополнительных параметров")
            print()
            print("💡 РЕКОМЕНДАЦИИ:")
            print("- Проверить правильность пароля в IIKo Office")
            print("- Убедиться что аккаунт активен")
            print("- Попробовать сбросить пароль")
            print("- Связаться с поддержкой IIKo для проверки аккаунта")
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())