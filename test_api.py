#!/usr/bin/env python3
"""
Test script for Gemini API Server
"""

import json
import requests
import time

BASE_URL = "http://localhost:50014"


def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_models():
    """Test models endpoint"""
    print("\n🔍 Testing models endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/v1/models", timeout=10)
        print(f"✅ Models endpoint: {response.status_code}")
        
        if response.status_code == 200:
            models = response.json()
            print(f"   Available models: {len(models['data'])}")
            for model in models['data']:
                print(f"   - {model['id']}")
        else:
            print(f"   Error: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Models test failed: {e}")
        return False


def test_chat_completion(model: str = "gemini-2.5-flash", stream: bool = False):
    """Test chat completion endpoint"""
    print(f"\n🔍 Testing chat completion (model: {model}, stream: {stream})...")
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Hello! Please respond with a short greeting."}
        ],
        "stream": stream
    }
    
    try:
        if stream:
            response = requests.post(
                f"{BASE_URL}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
                stream=True,
                timeout=30
            )
            
            print(f"✅ Chat completion (streaming): {response.status_code}")
            
            if response.status_code == 200:
                print("   Streaming response:")
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]  # Remove 'data: ' prefix
                            if data_str.strip() == '[DONE]':
                                print("   [DONE]")
                                break
                            try:
                                data = json.loads(data_str)
                                if 'choices' in data and data['choices']:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        print(f"   {delta['content']}", end='', flush=True)
                            except json.JSONDecodeError:
                                pass
                print()  # New line after streaming
            else:
                print(f"   Error: {response.text}")
        else:
            response = requests.post(
                f"{BASE_URL}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"✅ Chat completion (non-streaming): {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and result['choices']:
                    content = result['choices'][0]['message']['content']
                    print(f"   Response: {content}")
                    print(f"   Usage: {result.get('usage', {})}")
                else:
                    print(f"   Unexpected response format: {result}")
            else:
                print(f"   Error: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Chat completion test failed: {e}")
        return False


def test_openai_compatibility():
    """Test OpenAI library compatibility"""
    print("\n🔍 Testing OpenAI library compatibility...")
    
    try:
        import openai
        
        client = openai.OpenAI(
            api_key="dummy",  # Not used but required
            base_url=f"{BASE_URL}/v1"
        )
        
        # Test models
        models = client.models.list()
        print(f"✅ OpenAI client models: {len(models.data)} models found")
        
        # Test chat completion
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[
                {"role": "user", "content": "Say 'Hello from OpenAI client!'"}
            ]
        )
        
        print(f"✅ OpenAI client chat: {response.choices[0].message.content}")
        return True
        
    except ImportError:
        print("⚠️  OpenAI library not installed, skipping compatibility test")
        print("   Install with: pip install openai")
        return True
    except Exception as e:
        print(f"❌ OpenAI compatibility test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Starting Gemini API Server Tests")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Models Endpoint", test_models),
        ("Chat Completion (Non-streaming)", lambda: test_chat_completion(stream=False)),
        ("Chat Completion (Streaming)", lambda: test_chat_completion(stream=True)),
        ("OpenAI Compatibility", test_openai_compatibility),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
        
        time.sleep(1)  # Small delay between tests
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Your Gemini API server is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
        print("\nTroubleshooting tips:")
        print("1. Make sure the server is running: docker-compose up -d")
        print("2. Check server logs: docker-compose logs -f")
        print("3. Verify your cookies are valid and not expired")
        print("4. Check health endpoint: curl http://localhost:50014/health")


if __name__ == "__main__":
    main()
