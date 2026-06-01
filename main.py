#!/usr/bin/env python3
"""
Main entry point for Lab 3 - Weather Agent
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider
from src.core.openrouter_provider import OpenRouterProvider
from src.agent.agent import ReActAgent
from src.tools.weather_tools import WEATHER_TOOLS

def main():
    print("=" * 60)
    print("Weather Assistant Agent - Lab 3")
    print("=" * 60)
    
    # Lấy config từ environment
    provider = os.getenv("DEFAULT_PROVIDER", "openrouter")
    
    print(f"Provider: {provider}")
    print("-" * 60)
    
    # Khởi tạo LLM dựa trên provider
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("DEFAULT_MODEL", "gpt-4o")
        if not api_key:
            print("❌ Lỗi: OPENAI_API_KEY không được cấu hình")
            return
        print(f"Model: {model}")
        llm = OpenAIProvider(model_name=model, api_key=api_key)
    
    elif provider == "google":
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("DEFAULT_MODEL", "gemini-1.5-flash")
        if not api_key:
            print("❌ Lỗi: GEMINI_API_KEY không được cấu hình")
            print("Đăng ký key free tại: https://aistudio.google.com/app/apikey")
            return
        print(f"Model: {model}")
        llm = GeminiProvider(model_name=model, api_key=api_key)
    
    elif provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        model = os.getenv("OPENROUTER_MODEL", "google/gemma-4-31b-it")
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        
        if not api_key:
            print("❌ Lỗi: OPENROUTER_API_KEY không được cấu hình")
            print("Vui lòng thêm OPENROUTER_API_KEY vào file .env")
            return
        
        print(f"Model: {model}")
        print(f"Base URL: {base_url}")
        llm = OpenRouterProvider(
            model_name=model, 
            api_key=api_key,
            base_url=base_url
        )
    
    elif provider == "local":
        print("Local provider chưa được implement")
        return
    
    else:
        print(f"❌ Provider không hợp lệ: {provider}")
        print("Các lựa chọn: openai, google, openrouter, local")
        return
    
    print(f"Tools: {[t['name'] for t in WEATHER_TOOLS]}")
    print("-" * 60)
    
    agent = ReActAgent(llm=llm, tools=WEATHER_TOOLS, max_steps=5)
    
    # Test cases
    test_queries = [
        "What's the current weather in Hanoi?",
        "Should I bring an umbrella tomorrow in Da Nang?",
        "Compare the weather between Ho Chi Minh City and Hanoi",
        "It's 32 degrees and sunny, what should I wear?",
        "What's the weather forecast for the next 2 days in Da Nang?"
    ]
    
    print("\nRunning test cases...\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"TEST CASE {i}: {query}")
        print(f"{'='*60}")
        
        try:
            response = agent.run(query)
            print("\n🤖 AGENT RESPONSE:")
            print(str(response))
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print(f"\n{'-'*60}")

if __name__ == "__main__":
    main()