import requests
import json

def test_non_pro_access():
    """Test that non-PRO users cannot access PRO AI functions"""
    print("🔒 Testing PRO AI access control for non-PRO users...")
    
    base_url = "https://cursor-push.preview.emergentagent.com/api"
    
    # Create a free tier user
    user_data = {
        "email": "free_user_test@example.com",
        "name": "Free User Test",
        "city": "moskva"
    }
    
    response = requests.post(f"{base_url}/register", json=user_data)
    if response.status_code == 200:
        user_info = response.json()
        free_user_id = user_info["id"]
        print(f"   Created free user with ID: {free_user_id}")
    elif response.status_code == 400:
        # User already exists, get the user
        response = requests.get(f"{base_url}/user/free_user_test@example.com")
        if response.status_code == 200:
            user_info = response.json()
            free_user_id = user_info["id"]
            print(f"   Using existing free user with ID: {free_user_id}")
        else:
            print("   Failed to get free user")
            return False
    else:
        print(f"   Failed to create free user: {response.status_code}")
        return False
    
    # Sample tech card
    sample_tech_card = "**Название:** Test Dish\n**Категория:** основное\n**Описание:** Test description"
    
    # Test all PRO AI endpoints with free user
    endpoints = [
        "generate-sales-script",
        "generate-food-pairing", 
        "generate-photo-tips"
    ]
    
    all_blocked = True
    
    for endpoint in endpoints:
        request_data = {
            "user_id": free_user_id,
            "tech_card": sample_tech_card
        }
        
        response = requests.post(f"{base_url}/{endpoint}", json=request_data)
        
        if response.status_code == 403:
            print(f"   ✅ {endpoint}: Correctly blocked (403)")
        else:
            print(f"   ❌ {endpoint}: Not blocked (got {response.status_code})")
            all_blocked = False
    
    return all_blocked

if __name__ == "__main__":
    success = test_non_pro_access()
    if success:
        print("\n🎉 Access control working correctly - all PRO AI functions blocked for free users")
    else:
        print("\n⚠️ Access control issue - some PRO AI functions not properly blocked")
    exit(0 if success else 1)