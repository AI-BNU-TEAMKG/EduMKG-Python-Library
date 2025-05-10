import os

# --- API Keys ---
# It's highly recommended to use environment variables for API keys
# or a more secure configuration management system.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "YOUR_GOOGLE_API_KEY_HERE") 
OPENAI_API_KEY = os.getenv("", "")
OPENAI_BASE_URL = ""
BAIDU_TRANSLATE_APPID = os.getenv("BAIDU_TRANSLATE_APPID", "")
BAIDU_TRANSLATE_APPKEY = os.getenv("BAIDU_TRANSLATE_APPKEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "YOUR_OPENAI_COMPATIBLE_ENDPOINT_HERE") # e.g., for TTS
MULTIMODAL_LLM_URL = os.getenv("MULTIMODAL_LLM_URL", "YOUR_MULTIMODAL_API_ENDPOINT")
MULTIMODAL_LLM_AUTH_TOKEN = os.getenv("MULTIMODAL_LLM_AUTH_TOKEN", "YOUR_MULTIMODAL_API_TOKEN")
PDF_IMAGE_EXTRACT_URL = os.getenv("PDF_IMAGE_EXTRACT_URL", "YOUR_PDF_IMAGE_EXTRACT_SERVICE_URL")


# --- Proxy Settings ---
HTTP_PROXY = os.getenv("HTTP_PROXY", "http://127.0.0.1:7890")
HTTPS_PROXY = os.getenv("HTTPS_PROXY", "http://127.0.0.1:7890")

# --- LLM Settings ---
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v3" 
DEFAULT_GPT_MODEL = "gpt-4o-mini" 
DEFAULT_MULTIMODAL_MODEL = "gpt-4o" 
DEFAULT_TTS_MODEL = "tts-1"
DEFAULT_TTS_VOICE = ""

# --- Processing Parameters ---
NER_K_ITERATIONS = 3 # Default for self-refine
LLM_SEMANTIC_INTEGRATION_MAX_CALLS = 1450 # From Dataprocess.py
API_RETRY_DELAY_SECONDS = 2
API_MAX_RETRIES = 5
API_CALL_TIMEOUT_SECONDS = 70 # General timeout for LLM calls

# --- File Paths (These should ideally be passed as arguments to functions) ---
# Example:
# DEFAULT_OUTPUT_DIR = "output_data"

# --- Dashscope (if used) ---
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")


def setup_proxies():
    """Sets up proxy environment variables if specified in config."""
    if HTTP_PROXY:
        os.environ["http_proxy"] = HTTP_PROXY
    if HTTPS_PROXY:
        os.environ["https_proxy"] = HTTPS_PROXY

def configure_google_genai():
    """Configures the Google Generative AI client."""
    if GOOGLE_API_KEY != "YOUR_GOOGLE_API_KEY_HERE":
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)

def configure_dashscope():
    """Configures Dashscope if API key is provided."""
    if DASHSCOPE_API_KEY:
        import dashscope
        dashscope.api_key = DASHSCOPE_API_KEY

# Initial setup when config is imported
setup_proxies()
configure_google_genai()
configure_dashscope()