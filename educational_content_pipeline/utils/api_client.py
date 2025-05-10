import requests
import json
import time
import base64
from typing import List, Dict, Any, Optional, Tuple
from .. import config # Use relative import for config

# Placeholder for a more robust API client class or set of functions
# This would consolidate LLM calls from NER.py, ImageAligment.py, etc.

class LLMClient:
    def __init__(self):
        self.chatfire_api_key = config.CHATFIRE_API_KEY
        self.chatfire_base_url = config.CHATFIRE_BASE_URL
        self.multimodal_llm_url = config.MULTIMODAL_LLM_URL
        self.multimodal_llm_auth_token = config.MULTIMODAL_LLM_AUTH_TOKEN
        self.openai_api_key = config.OPENAI_API_KEY
        self.openai_base_url = config.OPENAI_BASE_URL

    def _make_request(self, url: str, headers: Dict, data: Dict, method: str = "POST",
                      max_retries: int = config.API_MAX_RETRIES,
                      retry_delay: int = config.API_RETRY_DELAY_SECONDS,
                      timeout: int = config.API_CALL_TIMEOUT_SECONDS) -> Optional[Dict]:
        for attempt in range(max_retries):
            try:
                response = requests.request(method, url, headers=headers, json=data, timeout=timeout, verify=False) # verify=False is generally not recommended for production
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"API request to {url} failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt)) # Exponential backoff
                else:
                    print(f"Max retries reached for {url}.")
                    return None
        return None # Should not be reached if loop completes normally

    def call_chatfire(self, model: str, content: str, role: str = "user") -> Optional[str]:
        """Calls the Chatfire API (e.g., for DeepSeek, GPT)."""
        if not self._api_key or self.chatfire_api_key == "": # Placeholder check
            return None

        payload = {
            "model": model,
            "messages": [{"role": role, "content": content}]
        }
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.chatfire_api_key}',
            'Content-Type': 'application/json'
        }
        
        print(f"Calling Chatfire: model={model}, content length={len(content)}")
        time.sleep(2) # Original sleep
        response_json = self._make_request(self.chatfire_base_url, headers, payload)

        if response_json and "choices" in response_json and response_json["choices"]:
            return response_json["choices"][0]["message"]["content"]
        else:
            print(f"Error or unexpected response from Chatfire: {response_json}")
            return None

    def call_google_gemini(self, model_name: str, content: str) -> Optional[str]:
        """Calls Google Gemini API."""
        try:
            import google.generativeai as genai
            if not config.GOOGLE_API_KEY or config.GOOGLE_API_KEY == "YOUR_GOOGLE_API_KEY_HERE":
                 print("Google API Key not configured or is a placeholder.")
                 return None
            
            # Ensure genai is configured (might have been done in config.py)
            if not genai.API_KEY: # Check if API key is set
                genai.configure(api_key=config.GOOGLE_API_KEY)

            model = genai.GenerativeModel(model_name)
            print(f"Calling Gemini: model={model_name}, content length={len(content)}")
            response = model.generate_content(content)
            return response.text
        except Exception as e:
            print(f"Error calling Google Gemini: {e}")
            return None

    def call_multimodal_llm(self, model: str, prompt: str, image_path: str) -> Optional[str]:
        """Calls a generic multimodal LLM API."""
        if not self.multimodal_llm_url or self.multimodal_llm_url == "YOUR_MULTIMODAL_API_ENDPOINT":
            print("Multimodal LLM URL not configured or is a placeholder.")
            return None
        if not self.multimodal_llm_auth_token or self.multimodal_llm_auth_token == "YOUR_MULTIMODAL_API_TOKEN":
            print("Multimodal LLM Auth Token not configured or is a placeholder.")
            return None
            
        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            print(f"Error reading or encoding image {image_path}: {e}")
            return None

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                    ],
                }
            ]
        }
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.multimodal_llm_auth_token}', # Assuming Bearer token
            'Content-Type': 'application/json'
        }
        
        print(f"Calling Multimodal LLM: model={model}, image={image_path}")
        # Add retries similar to _make_request or integrate into it
        for attempt in range(config.API_MAX_RETRIES):
            try:
                response = requests.post(self.multimodal_llm_url, headers=headers, json=payload, timeout=config.API_CALL_TIMEOUT_SECONDS + 30) # Longer timeout for image uploads
                response.raise_for_status()
                response_json = response.json()
                if response_json and "choices" in response_json and response_json["choices"]:
                    return response_json["choices"][0]["message"]["content"]
            except requests.exceptions.RequestException as e:
                print(f"Multimodal API request failed (attempt {attempt + 1}/{config.API_MAX_RETRIES}): {e}")
                if attempt < config.API_MAX_RETRIES -1:
                     time.sleep(config.API_RETRY_DELAY_SECONDS * (2**attempt) + 60) # Longer backoff
                else:
                    print("Max retries reached for multimodal API.")
                    return None
        return None


# Initialize a default client instance for easy import
llm_client = LLMClient()