import wikipediaapi
import time
import requests # For session with proxy
from typing import Optional, Dict
from .translation import baidu_translate_text # Relative import
from .. import config # Relative import

class WikipediaService:
    def __init__(self, language: str = "en", user_agent: str = "EdContentPipeline/0.1 (botframework@example.com)"):
        self.language = language
        self.user_agent = user_agent
        self.wiki_api = self._setup_wiki_api()

    def _setup_wiki_api(self):
        session = requests.Session()
        if config.HTTP_PROXY or config.HTTPS_PROXY:
            proxies = {}
            if config.HTTP_PROXY: proxies['http'] = config.HTTP_PROXY
            if config.HTTPS_PROXY: proxies['https'] = config.HTTPS_PROXY
            session.proxies = proxies
        
        # wikipediaapi uses its own session internally, we need to patch it or use its mechanism
        # For wikipediaapi, you pass the session to the constructor
        wiki = wikipediaapi.Wikipedia(
            language=self.language,
            user_agent=self.user_agent,
            session=session # Pass the custom session here
        )
        return wiki

    def get_summary(self, concept_term_native_lang: str, translate_to_en_first: bool = True) -> Optional[str]:
        """
        Fetches a Wikipedia summary for a concept.
        If translate_to_en_first is True (and concept is not English), it translates first.
        """
        search_term = concept_term_native_lang
        if translate_to_en_first and self.language == "en": # Assuming concepts are Chinese if native_lang is not en
            # Check if concept_term_native_lang is likely Chinese to avoid unnecessary translation
            if any('\u4e00' <= char <= '\u9fff' for char in concept_term_native_lang):
                translated_term = baidu_translate_text(concept_term_native_lang, from_lang='zh', to_lang='en')
                if not translated_term:
                    print(f"Translation failed for '{concept_term_native_lang}', trying original term.")
                else:
                    search_term = translated_term
                    print(f"Translated '{concept_term_native_lang}' to '{search_term}' for Wikipedia search.")
            else: # Assuming it's already in English or target language
                pass


        max_retries = config.API_MAX_RETRIES
        retry_delay_base = config.API_RETRY_DELAY_SECONDS

        for attempt in range(max_retries):
            try:
                page = self.wiki_api.page(search_term)
                if page.exists():
                    print(f"Found Wikipedia page for '{search_term}'. Summary length: {len(page.summary)}")
                    return page.summary # Returns first section by default
                else:
                    print(f"Wikipedia page not found for '{search_term}' (in {self.language}).")
                    return "not found" # Explicitly return "not found"
            except Exception as e: # More specific exceptions can be caught from requests or wikipediaapi
                print(f"Error fetching Wikipedia page for '{search_term}' (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay_base * (2 ** attempt)) # Exponential backoff
                else:
                    print(f"Max retries reached for Wikipedia search of '{search_term}'.")
                    return "error" # Explicitly return "error"
        return "error" # Should be caught by loop end

# Example usage:
# wiki_service = WikipediaService()
# summary = wiki_service.get_summary("细胞核")