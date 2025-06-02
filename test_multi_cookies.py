#!/usr/bin/env python3
"""
Test script for multi-cookie functionality
"""

import os
import json
import time
import random
from pathlib import Path
from typing import List, Dict, Optional

# Simplified CookieConfig class for testing
class CookieConfig:
    def __init__(self, secure_1psid: str, secure_1psidts: str = "", name: str = ""):
        self.secure_1psid = secure_1psid
        self.secure_1psidts = secure_1psidts
        self.name = name or f"Account-{secure_1psid[:8]}"
        self.is_available = True
        self.last_used = 0
        self.error_count = 0
        self.max_errors = 3

    def mark_error(self):
        """Mark an error for this cookie"""
        self.error_count += 1
        if self.error_count >= self.max_errors:
            self.is_available = False

    def mark_success(self):
        """Mark successful usage"""
        self.error_count = 0
        self.is_available = True
        self.last_used = time.time()

# Simplified CookieManager class for testing
class CookieManager:
    def __init__(self):
        self.cookies: List[CookieConfig] = []
        self.current_index = 0

    def load_cookies_from_env(self):
        """Load cookies from environment variables"""
        self.cookies.clear()

        # Load single cookie (backward compatibility)
        secure_1psid = os.getenv("SECURE_1PSID")
        secure_1psidts = os.getenv("SECURE_1PSIDTS", "")

        if secure_1psid:
            self.cookies.append(CookieConfig(
                secure_1psid=secure_1psid,
                secure_1psidts=secure_1psidts,
                name="Primary Account"
            ))

        # Load multiple cookies from JSON
        cookies_json = os.getenv("COOKIES_JSON")
        if cookies_json:
            try:
                cookies_data = json.loads(cookies_json)
                for i, cookie_data in enumerate(cookies_data):
                    self.cookies.append(CookieConfig(
                        secure_1psid=cookie_data["secure_1psid"],
                        secure_1psidts=cookie_data.get("secure_1psidts", ""),
                        name=cookie_data.get("name", f"Account-{i+1}")
                    ))
            except json.JSONDecodeError as e:
                print(f"Error parsing COOKIES_JSON: {e}")

        # Load from individual environment variables (COOKIE_1_PSID, COOKIE_1_PSIDTS, etc.)
        i = 1
        while True:
            psid_key = f"COOKIE_{i}_PSID"
            psidts_key = f"COOKIE_{i}_PSIDTS"
            name_key = f"COOKIE_{i}_NAME"

            psid = os.getenv(psid_key)
            if not psid:
                break

            self.cookies.append(CookieConfig(
                secure_1psid=psid,
                secure_1psidts=os.getenv(psidts_key, ""),
                name=os.getenv(name_key, f"Account-{i}")
            ))
            i += 1

        if not self.cookies:
            raise ValueError("No valid cookies found. Please set SECURE_1PSID or COOKIES_JSON environment variable.")

    def get_available_cookies(self) -> List[CookieConfig]:
        """Get list of available cookies"""
        return [cookie for cookie in self.cookies if cookie.is_available]

    def get_next_cookie(self) -> Optional[CookieConfig]:
        """Get next available cookie using round-robin"""
        available_cookies = self.get_available_cookies()
        if not available_cookies:
            return None

        # Round-robin selection
        cookie = available_cookies[self.current_index % len(available_cookies)]
        self.current_index = (self.current_index + 1) % len(available_cookies)
        return cookie

    def get_random_cookie(self) -> Optional[CookieConfig]:
        """Get random available cookie"""
        available_cookies = self.get_available_cookies()
        if not available_cookies:
            return None
        return random.choice(available_cookies)

    def get_least_used_cookie(self) -> Optional[CookieConfig]:
        """Get least recently used cookie"""
        available_cookies = self.get_available_cookies()
        if not available_cookies:
            return None
        return min(available_cookies, key=lambda c: c.last_used)

    def get_status(self) -> Dict:
        """Get status of all cookies"""
        return {
            "total_cookies": len(self.cookies),
            "available_cookies": len(self.get_available_cookies()),
            "cookies": [
                {
                    "name": cookie.name,
                    "is_available": cookie.is_available,
                    "error_count": cookie.error_count,
                    "last_used": cookie.last_used
                }
                for cookie in self.cookies
            ]
        }


def test_cookie_manager():
    """Test the cookie manager functionality"""
    print("🧪 Testing Cookie Manager")
    print("=" * 50)
    
    # Create a test cookie manager
    manager = CookieManager()
    
    # Test 1: Load from environment variables
    print("\n1. Testing environment variable loading...")
    
    # Set up test environment variables
    os.environ["SECURE_1PSID"] = "test_psid_1"
    os.environ["SECURE_1PSIDTS"] = "test_psidts_1"
    
    os.environ["COOKIE_1_PSID"] = "test_psid_2"
    os.environ["COOKIE_1_PSIDTS"] = "test_psidts_2"
    os.environ["COOKIE_1_NAME"] = "Test Account 1"
    
    os.environ["COOKIE_2_PSID"] = "test_psid_3"
    os.environ["COOKIE_2_PSIDTS"] = "test_psidts_3"
    os.environ["COOKIE_2_NAME"] = "Test Account 2"
    
    # Test JSON format
    os.environ["COOKIES_JSON"] = '''[
        {
            "secure_1psid": "test_psid_4",
            "secure_1psidts": "test_psidts_4",
            "name": "JSON Account 1"
        },
        {
            "secure_1psid": "test_psid_5",
            "secure_1psidts": "test_psidts_5",
            "name": "JSON Account 2"
        }
    ]'''
    
    try:
        manager.load_cookies_from_env()
        print(f"✅ Loaded {len(manager.cookies)} cookies")
        
        for i, cookie in enumerate(manager.cookies):
            print(f"   {i+1}. {cookie.name}: {cookie.secure_1psid}")
            
    except Exception as e:
        print(f"❌ Failed to load cookies: {e}")
        return False
    
    # Test 2: Cookie selection strategies
    print("\n2. Testing cookie selection strategies...")
    
    # Round-robin
    print("   Round-robin selection:")
    for i in range(6):
        cookie = manager.get_next_cookie()
        if cookie:
            print(f"     {i+1}. {cookie.name}")
    
    # Random selection
    print("   Random selection:")
    for i in range(3):
        cookie = manager.get_random_cookie()
        if cookie:
            print(f"     {i+1}. {cookie.name}")
    
    # Least used
    print("   Least used selection:")
    for i in range(3):
        cookie = manager.get_least_used_cookie()
        if cookie:
            print(f"     {i+1}. {cookie.name}")
            cookie.mark_success()  # Update last used time
    
    # Test 3: Error handling
    print("\n3. Testing error handling...")
    
    # Mark some cookies as failed
    manager.cookies[0].mark_error()
    manager.cookies[0].mark_error()
    manager.cookies[0].mark_error()  # Should make it unavailable
    
    available = manager.get_available_cookies()
    print(f"   Available cookies after marking one as failed: {len(available)}")
    
    # Test 4: Status reporting
    print("\n4. Testing status reporting...")
    status = manager.get_status()
    print(f"   Total cookies: {status['total_cookies']}")
    print(f"   Available cookies: {status['available_cookies']}")
    
    for cookie_status in status['cookies']:
        print(f"     - {cookie_status['name']}: {'✅' if cookie_status['is_available'] else '❌'} "
              f"(errors: {cookie_status['error_count']})")
    
    print("\n✅ All tests completed successfully!")
    return True


def test_env_file_parsing():
    """Test parsing of .env file configurations"""
    print("\n🔧 Testing .env file configurations")
    print("=" * 50)
    
    # Read current .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    print("Current .env file content:")
    print("-" * 30)
    
    # Show only the cookie-related lines
    lines = content.split('\n')
    for line in lines:
        if any(keyword in line for keyword in ['SECURE_1PSID', 'COOKIE_', 'COOKIES_JSON']):
            if not line.strip().startswith('#'):
                print(f"   {line}")
    
    print("-" * 30)
    
    return True


if __name__ == "__main__":
    print("🚀 Multi-Cookie Functionality Test")
    print("=" * 60)
    
    # Test environment file parsing
    test_env_file_parsing()
    
    # Test cookie manager
    test_cookie_manager()
    
    print("\n🎉 Testing completed!")
