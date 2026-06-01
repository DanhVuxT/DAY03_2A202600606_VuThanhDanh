import requests
import time
import json
from typing import Optional

class OpenRouterProvider:
    def __init__(self, 
                 model_name: str = "google/gemma-4-31b-it", 
                 api_key: Optional[str] = None,
                 base_url: str = "https://openrouter.ai/api/v1"):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> dict:
        start_time = time.time()
        
        # Xây dựng messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions", 
                headers=headers, 
                json=payload,
                timeout=60
            )
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return {
                    "content": content,
                    "latency_ms": latency_ms,
                    "model": self.model_name
                }
            else:
                error_msg = f"OpenRouter API Error: {response.status_code} - {response.text}"
                print(error_msg)  # In ra để debug
                return {
                    "content": error_msg,
                    "latency_ms": latency_ms,
                    "error": error_msg
                }
        except requests.exceptions.Timeout:
            latency_ms = (time.time() - start_time) * 1000
            return {
                "content": "Lỗi: Request timeout sau 60 giây",
                "latency_ms": latency_ms,
                "error": "timeout"
            }
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return {
                "content": f"Lỗi kết nối OpenRouter: {str(e)}",
                "latency_ms": latency_ms,
                "error": str(e)
            }