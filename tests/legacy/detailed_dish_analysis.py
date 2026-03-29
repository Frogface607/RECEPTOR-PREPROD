#!/usr/bin/env python3
"""
Detailed IIKo DISH Creation Analysis - Get Full Response Details
"""

import requests
import json
import time
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def log_test(message):
    """Log test messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def detailed_dish_analysis():
    """Get detailed response analysis"""
    log_test("🔍 DETAILED DISH CREATION ANALYSIS")
    log_test("=" * 80)
    
    # Test data from review request
    test_data = {
        "name": "Исправленное тестовое блюдо",
        "organization_id": "default-org-001", 
        "description": "Тест с исправленной структурой ProductDto",
        "ingredients": [
            {"name": "Мука", "quantity": 200, "unit": "г"},
            {"name": "Яйца", "quantity": 2, "unit": "шт"}
        ],
        "preparation_steps": ["Смешать ингредиенты", "Выпекать 30 минут"],
        "weight": 300.0,
        "price": 450.0
    }
    
    try:
        url = f"{API_BASE}/iiko/products/create-complete-dish"
        log_test(f"🔗 Making request to: {url}")
        
        response = requests.post(url, json=test_data, timeout=60)
        log_test(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                log_test("📄 FULL RESPONSE CONTENT:")
                log_test(json.dumps(data, indent=2, ensure_ascii=False))
                
                return data
                
            except json.JSONDecodeError as e:
                log_test(f"❌ JSON parsing failed: {str(e)}")
                log_test(f"📄 Raw response: {response.text}")
                return None
                
        elif response.status_code == 422:
            log_test("❌ HTTP 422 - Validation Error")
            try:
                error_data = response.json()
                log_test("📄 VALIDATION ERROR DETAILS:")
                log_test(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                log_test(f"📄 Raw error response: {response.text}")
            return None
        else:
            log_test(f"❌ HTTP Error: {response.status_code}")
            log_test(f"📄 Error response: {response.text}")
            return None
            
    except Exception as e:
        log_test(f"❌ Request failed: {str(e)}")
        return None

def test_backend_logs():
    """Check backend logs for more details"""
    log_test("\n📋 CHECKING BACKEND LOGS")
    log_test("=" * 80)
    
    try:
        # Check supervisor logs
        import subprocess
        result = subprocess.run(['tail', '-n', '50', '/var/log/supervisor/backend.out.log'], 
                              capture_output=True, text=True, timeout=10)
        if result.stdout:
            log_test("📄 BACKEND LOGS (last 50 lines):")
            log_test(result.stdout)
        else:
            log_test("📄 No backend logs found or accessible")
            
    except Exception as e:
        log_test(f"❌ Could not access backend logs: {str(e)}")

def main():
    """Main analysis function"""
    log_test("🚀 STARTING DETAILED IIKO DISH ANALYSIS")
    log_test("=" * 80)
    
    # Get detailed response
    result = detailed_dish_analysis()
    
    # Check backend logs
    test_backend_logs()
    
    log_test("\n🏁 DETAILED ANALYSIS COMPLETED")

if __name__ == "__main__":
    main()