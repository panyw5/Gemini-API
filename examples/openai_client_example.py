#!/usr/bin/env python3
"""
Example usage of Gemini API Server with OpenAI client library
"""

from typing import List, Dict, Any

try:
    import openai
except ImportError:
    print("Please install openai library: pip install openai")
    exit(1)


class GeminiOpenAIClient:
    """Wrapper for OpenAI client to use with Gemini API Server"""
    
    def __init__(self, base_url: str = "http://localhost:50014/v1"):
        self.client = openai.OpenAI(
            api_key="dummy",  # Not used but required by OpenAI client
            base_url=base_url
        )
    
    def list_models(self) -> List[str]:
        """List available models"""
        models = self.client.models.list()
        return [model.id for model in models.data]
    
    def chat(self, 
             messages: List[Dict[str, str]], 
             model: str = "gemini-2.5-flash",
             stream: bool = False,
             **kwargs) -> Any:
        """Send chat completion request"""
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream,
            **kwargs
        )


def example_basic_chat():
    """Basic chat example"""
    print("🤖 Basic Chat Example")
    print("=" * 30)
    
    client = GeminiOpenAIClient()
    
    # List available models
    print("Available models:")
    models = client.list_models()
    for model in models:
        print(f"  - {model}")
    
    print("\n" + "-" * 30)
    
    # Simple chat
    messages = [
        {"role": "user", "content": "Hello! Please introduce yourself briefly."}
    ]
    
    response = client.chat(messages, model="gemini-2.5-flash")
    print(f"User: {messages[0]['content']}")
    print(f"Assistant: {response.choices[0].message.content}")


def example_conversation():
    """Multi-turn conversation example"""
    print("\n🗣️  Conversation Example")
    print("=" * 30)
    
    client = GeminiOpenAIClient()
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant that answers questions about Python programming."},
        {"role": "user", "content": "What is a list comprehension in Python?"}
    ]
    
    # First message
    response = client.chat(messages, model="gemini-2.5-pro")
    assistant_response = response.choices[0].message.content
    
    print(f"User: {messages[1]['content']}")
    print(f"Assistant: {assistant_response}")
    
    # Add assistant response to conversation
    messages.append({"role": "assistant", "content": assistant_response})
    
    # Follow-up question
    messages.append({"role": "user", "content": "Can you give me a practical example?"})
    
    response = client.chat(messages, model="gemini-2.5-pro")
    print(f"\nUser: {messages[-1]['content']}")
    print(f"Assistant: {response.choices[0].message.content}")


def example_streaming():
    """Streaming response example"""
    print("\n🌊 Streaming Example")
    print("=" * 30)
    
    client = GeminiOpenAIClient()
    
    messages = [
        {"role": "user", "content": "Tell me a short story about a robot learning to paint."}
    ]
    
    print(f"User: {messages[0]['content']}")
    print("Assistant: ", end="", flush=True)
    
    # Stream the response
    stream = client.chat(messages, model="gemini-2.5-flash", stream=True)
    
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="", flush=True)
    
    print()  # New line after streaming


def example_different_models():
    """Test different models"""
    print("\n🎯 Different Models Example")
    print("=" * 30)
    
    client = GeminiOpenAIClient()
    
    prompt = "Explain quantum computing in one sentence."
    models_to_test = ["gemini-2.5-flash", "gemini-2.5-pro"]
    
    for model in models_to_test:
        try:
            print(f"\nTesting {model}:")
            messages = [{"role": "user", "content": prompt}]
            response = client.chat(messages, model=model)
            print(f"Response: {response.choices[0].message.content}")
        except Exception as e:
            print(f"Error with {model}: {e}")


def example_with_system_prompt():
    """Example with system prompt"""
    print("\n⚙️  System Prompt Example")
    print("=" * 30)
    
    client = GeminiOpenAIClient()
    
    messages = [
        {
            "role": "system", 
            "content": "You are a pirate captain. Respond to all questions in pirate speak with nautical metaphors."
        },
        {
            "role": "user", 
            "content": "How do I learn programming?"
        }
    ]
    
    response = client.chat(messages, model="gemini-2.5-flash")
    
    print(f"System: {messages[0]['content']}")
    print(f"User: {messages[1]['content']}")
    print(f"Assistant: {response.choices[0].message.content}")


def main():
    """Run all examples"""
    print("🚀 Gemini API Server - OpenAI Client Examples")
    print("=" * 50)
    
    try:
        # Test connection first
        client = GeminiOpenAIClient()
        models = client.list_models()
        print(f"✅ Connected to Gemini API Server ({len(models)} models available)")
        
        # Run examples
        example_basic_chat()
        example_conversation()
        example_streaming()
        example_different_models()
        example_with_system_prompt()
        
        print("\n🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure the Gemini API server is running: docker-compose up -d")
        print("2. Check server health: curl http://localhost:50014/health")
        print("3. Verify your cookies are valid in the .env file")


if __name__ == "__main__":
    main()
