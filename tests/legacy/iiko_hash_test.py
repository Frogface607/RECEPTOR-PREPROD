#!/usr/bin/env python3
"""
IIKo Password Hashing Test
Testing different password hashing methods based on the error "Не указан hash пароля"
"""

import requests
import hashlib
import hmac
from datetime import datetime

# IIKo server details
IIKO_BASE_URL = "https://edison-bar.iiko.it"
LOGIN = "Sergey"
PASSWORD = "metkamfetamin"

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"[{timestamp}] {status_emoji} {test_name}: {status}")
    if details:
        print(f"    Details: {details}")
    print()

def generate_password_hashes(password):
    """Generate various hash formats for the password"""
    hashes = {}
    
    # MD5
    hashes['md5'] = hashlib.md5(password.encode()).hexdigest()
    hashes['md5_upper'] = hashlib.md5(password.encode()).hexdigest().upper()
    
    # SHA1
    hashes['sha1'] = hashlib.sha1(password.encode()).hexdigest()
    hashes['sha1_upper'] = hashlib.sha1(password.encode()).hexdigest().upper()
    
    # SHA256
    hashes['sha256'] = hashlib.sha256(password.encode()).hexdigest()
    hashes['sha256_upper'] = hashlib.sha256(password.encode()).hexdigest().upper()
    
    # Common variations with salt (using login as salt)
    login_salt = LOGIN.lower()
    hashes['md5_with_login_salt'] = hashlib.md5((password + login_salt).encode()).hexdigest()
    hashes['md5_with_login_salt_reverse'] = hashlib.md5((login_salt + password).encode()).hexdigest()
    
    # SHA1 with salt
    hashes['sha1_with_login_salt'] = hashlib.sha1((password + login_salt).encode()).hexdigest()
    hashes['sha1_with_login_salt_reverse'] = hashlib.sha1((login_salt + password).encode()).hexdigest()
    
    return hashes

def test_password_hashes():
    """Test different password hash formats"""
    print("🔐 TESTING PASSWORD HASH FORMATS")
    print("=" * 60)
    
    hashes = generate_password_hashes(PASSWORD)
    
    print(f"Generated hashes for password '{PASSWORD}':")
    for hash_type, hash_value in hashes.items():
        print(f"  {hash_type}: {hash_value}")
    print()
    
    success_found = False
    
    # Test each hash with different parameter names
    parameter_names = ['pass', 'password', 'hash', 'passwordHash', 'passHash']
    
    for param_name in parameter_names:
        print(f"Testing parameter name: '{param_name}'")
        
        for hash_type, hash_value in hashes.items():
            test_name = f"{param_name} with {hash_type}"
            
            try:
                params = {
                    "login": LOGIN,
                    param_name: hash_value
                }
                
                response = requests.get(f"{IIKO_BASE_URL}/resto/api/auth", params=params, timeout=10)
                
                if response.status_code == 200:
                    log_test(test_name, "PASS", f"Session key: {response.text[:50]}...")
                    print(f"🎉 SUCCESS! Found working method: {param_name}={hash_type}")
                    print(f"Hash value: {hash_value}")
                    success_found = True
                    return True
                elif response.status_code == 401:
                    error_msg = response.text
                    if "Неверный пароль" in error_msg:
                        log_test(test_name, "FAIL", "Wrong password (hash rejected)")
                    elif "hash пароля" in error_msg:
                        log_test(test_name, "FAIL", "Hash format issue")
                    else:
                        log_test(test_name, "FAIL", f"401: {error_msg}")
                else:
                    log_test(test_name, "FAIL", f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                log_test(test_name, "FAIL", f"Exception: {str(e)}")
        
        print()  # Separator between parameter names
    
    return success_found

def test_form_data_hashes():
    """Test password hashes with POST form data"""
    print("📝 TESTING FORM DATA WITH HASHES")
    print("=" * 60)
    
    hashes = generate_password_hashes(PASSWORD)
    
    # Test most common hash types with form data
    common_hashes = ['md5', 'sha1', 'md5_upper', 'sha1_upper']
    
    for hash_type in common_hashes:
        hash_value = hashes[hash_type]
        
        # Test with 'pass' parameter
        try:
            data = {
                "login": LOGIN,
                "pass": hash_value
            }
            
            response = requests.post(f"{IIKO_BASE_URL}/resto/api/auth", data=data, timeout=10)
            
            if response.status_code == 200:
                log_test(f"POST form {hash_type}", "PASS", f"Session key: {response.text[:50]}...")
                print(f"🎉 SUCCESS! Form data with {hash_type} hash worked!")
                return True
            elif response.status_code == 401:
                log_test(f"POST form {hash_type}", "FAIL", f"401: {response.text}")
            else:
                log_test(f"POST form {hash_type}", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            log_test(f"POST form {hash_type}", "FAIL", f"Exception: {str(e)}")
    
    return False

def test_special_iiko_hash():
    """Test IIKo-specific hash formats"""
    print("🏢 TESTING IIKO-SPECIFIC HASH FORMATS")
    print("=" * 60)
    
    # Some systems use login+password combinations
    special_combinations = [
        f"{LOGIN}:{PASSWORD}",
        f"{LOGIN.lower()}:{PASSWORD}",
        f"{PASSWORD}:{LOGIN}",
        f"{PASSWORD}:{LOGIN.lower()}",
    ]
    
    for combination in special_combinations:
        # Test MD5 and SHA1 of the combination
        md5_hash = hashlib.md5(combination.encode()).hexdigest()
        sha1_hash = hashlib.sha1(combination.encode()).hexdigest()
        
        for hash_type, hash_value in [('md5', md5_hash), ('sha1', sha1_hash)]:
            test_name = f"Special {hash_type} of '{combination}'"
            
            try:
                params = {
                    "login": LOGIN,
                    "pass": hash_value
                }
                
                response = requests.get(f"{IIKO_BASE_URL}/resto/api/auth", params=params, timeout=10)
                
                if response.status_code == 200:
                    log_test(test_name, "PASS", f"Session key: {response.text[:50]}...")
                    print(f"🎉 SUCCESS! Special combination worked: {combination} -> {hash_type}")
                    return True
                elif response.status_code == 401:
                    log_test(test_name, "FAIL", f"401: {response.text}")
                else:
                    log_test(test_name, "FAIL", f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                log_test(test_name, "FAIL", f"Exception: {str(e)}")
    
    return False

def main():
    """Run all password hashing tests"""
    print("🔍 IIKO PASSWORD HASHING AUTHENTICATION TESTING")
    print("=" * 80)
    print("🎯 GOAL: Find the correct password hash format for IIKo Office")
    print("🔑 CREDENTIALS: Sergey / metkamfetamin")
    print("💡 CLUE: Server says 'Не указан hash пароля' - needs hashed password!")
    print()
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = False
    
    try:
        # Test 1: Various password hash formats
        if not success:
            success = test_password_hashes()
        
        # Test 2: Form data with hashes
        if not success:
            success = test_form_data_hashes()
        
        # Test 3: IIKo-specific hash formats
        if not success:
            success = test_special_iiko_hash()
        
        print("🏁 PASSWORD HASHING TESTING COMPLETED")
        print("=" * 80)
        
        if success:
            print("🎉 SUCCESS: Found working password hash method!")
            print("💡 The backend should be updated to use this hash format")
        else:
            print("❌ FAILURE: No password hash method worked")
            print("💡 RECOMMENDATIONS:")
            print("   1. Contact IIKo support for correct hash format")
            print("   2. Check IIKo Office documentation")
            print("   3. Verify if there's a different authentication endpoint")
            print("   4. Consider if the account needs special permissions")
        
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {str(e)}")

if __name__ == "__main__":
    main()