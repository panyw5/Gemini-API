#!/usr/bin/env python3
"""
Demo script for multi-cookie functionality
This script demonstrates how to use the Gemini API server with multiple cookies
"""

import requests
import json
import time
from typing import Dict, Any


def test_api_endpoint(url: str, endpoint: str) -> Dict[str, Any]:
    """Test an API endpoint and return the response"""
    try:
        response = requests.get(f"{url}{endpoint}", timeout=10)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


def test_chat_completion(url: str, message: str, model: str = "gemini-2.5-flash") -> Dict[str, Any]:
    """Test chat completion endpoint"""
    try:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "stream": False
        }
        
        response = requests.post(
            f"{url}/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


def main():
    """Main demo function"""
    print("🚀 Gemini API 多 Cookies 功能演示")
    print("=" * 60)
    
    # API server URL
    api_url = "http://localhost:50014"
    
    print(f"📡 连接到 API 服务器: {api_url}")
    
    # Test 1: Check health
    print("\n1️⃣ 健康检查...")
    health_result = test_api_endpoint(api_url, "/health")
    if health_result["success"]:
        print("✅ 服务器运行正常")
    else:
        print(f"❌ 服务器连接失败: {health_result['error']}")
        return
    
    # Test 2: Check cookies status
    print("\n2️⃣ 检查 Cookies 状态...")
    cookies_result = test_api_endpoint(api_url, "/cookies/status")
    if cookies_result["success"]:
        status = cookies_result["data"]
        print(f"✅ 总共配置了 {status['total_cookies']} 个账户")
        print(f"✅ 当前可用 {status['available_cookies']} 个账户")
        
        print("\n账户详情:")
        for i, cookie in enumerate(status["cookies"], 1):
            status_icon = "✅" if cookie["is_available"] else "❌"
            print(f"   {i}. {cookie['name']}: {status_icon} (错误次数: {cookie['error_count']})")
    else:
        print(f"❌ 无法获取 cookies 状态: {cookies_result['error']}")
        return
    
    # Test 3: List available models
    print("\n3️⃣ 获取可用模型...")
    models_result = test_api_endpoint(api_url, "/v1/models")
    if models_result["success"]:
        models = models_result["data"]["data"]
        print(f"✅ 找到 {len(models)} 个可用模型:")
        for model in models[:3]:  # Show first 3 models
            print(f"   - {model['id']}")
        if len(models) > 3:
            print(f"   ... 还有 {len(models) - 3} 个模型")
    else:
        print(f"❌ 无法获取模型列表: {models_result['error']}")
    
    # Test 4: Multiple chat completions to test load balancing
    print("\n4️⃣ 测试负载均衡 (发送多个请求)...")
    
    test_messages = [
        "你好！请简单介绍一下自己。",
        "什么是人工智能？",
        "请推荐一本好书。",
        "今天天气怎么样？",
        "请解释一下机器学习的概念。"
    ]
    
    successful_requests = 0
    failed_requests = 0
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n   请求 {i}: {message[:20]}...")
        
        result = test_chat_completion(api_url, message)
        if result["success"]:
            response_text = result["data"]["choices"][0]["message"]["content"]
            print(f"   ✅ 成功 - 响应长度: {len(response_text)} 字符")
            successful_requests += 1
        else:
            print(f"   ❌ 失败: {result['error']}")
            failed_requests += 1
        
        # Small delay between requests
        time.sleep(1)
    
    # Test 5: Check cookies status after requests
    print(f"\n5️⃣ 请求完成后的 Cookies 状态...")
    print(f"   成功请求: {successful_requests}")
    print(f"   失败请求: {failed_requests}")
    
    cookies_result_after = test_api_endpoint(api_url, "/cookies/status")
    if cookies_result_after["success"]:
        status_after = cookies_result_after["data"]
        print(f"   当前可用账户: {status_after['available_cookies']}/{status_after['total_cookies']}")
        
        print("\n   账户使用情况:")
        for i, cookie in enumerate(status_after["cookies"], 1):
            status_icon = "✅" if cookie["is_available"] else "❌"
            last_used = time.strftime("%H:%M:%S", time.localtime(cookie["last_used"])) if cookie["last_used"] > 0 else "未使用"
            print(f"     {i}. {cookie['name']}: {status_icon} (最后使用: {last_used})")
    
    print("\n🎉 演示完成！")
    print("\n💡 提示:")
    print("   - 如果某个账户失效，系统会自动切换到其他账户")
    print("   - 可以通过 /cookies/status 端点监控账户状态")
    print("   - 支持轮询、随机、最少使用等负载均衡策略")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
