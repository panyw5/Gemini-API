#!/usr/bin/env python3
"""
Test script to check if Google cookies are valid
"""

import os
import asyncio
from src.gemini_webapi import GeminiClient

async def test_cookies():
    """Test if cookies are valid"""
    print("🔍 Testing Google cookies...")
    
    # Get cookies from environment
    secure_1psid = os.getenv("SECURE_1PSID")
    secure_1psidts = os.getenv("SECURE_1PSIDTS", "")
    
    if not secure_1psid:
        print("❌ SECURE_1PSID not found in environment")
        return False
    
    print(f"✅ SECURE_1PSID found: {secure_1psid[:20]}...")
    if secure_1psidts:
        print(f"✅ SECURE_1PSIDTS found: {secure_1psidts[:20]}...")
    else:
        print("⚠️  SECURE_1PSIDTS not provided")
    
    try:
        print("\n🔄 Initializing Gemini client...")
        client = GeminiClient(
            secure_1psid=secure_1psid,
            secure_1psidts=secure_1psidts,
            proxy=None
        )
        
        print("🔄 Attempting to initialize connection...")
        await client.init(timeout=30, auto_refresh=True)
        
        print("✅ Gemini client initialized successfully!")
        
        print("\n🔄 Testing content generation...")
        response = await client.generate_content("Hello! Please respond with 'Hi there!'")
        
        print(f"✅ Response received: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure you're logged into https://gemini.google.com")
        print("2. Get fresh cookies from your browser:")
        print("   - Press F12 -> Network tab -> Refresh page")
        print("   - Find any request and copy __Secure-1PSID and __Secure-1PSIDTS")
        print("3. Update your .env file with the new cookie values")
        print("4. Restart the container: docker-compose restart")
        return False

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    result = asyncio.run(test_cookies())
    if result:
        print("\n🎉 Cookies are valid! Your API should work correctly.")
    else:
        print("\n❌ Cookies are invalid. Please update them and try again.")
