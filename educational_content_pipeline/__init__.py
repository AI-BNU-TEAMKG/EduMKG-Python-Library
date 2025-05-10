# educational_content_pipeline/__init__.py

# Expose key classes or functions from submodules
from .utils.file_operations import get_filenames_recursive, read_json_file, write_json_file
from .utils.api_client import llm_client, LLMClient

from .dataprocess.audio_video import process_mp4_to_mp3_conversion, process_video_clipping
from .dataprocess.text_extraction import process_docx_to_timestamped_text
from .dataprocess.llm_segmentation import semantic_integrate_text_file, batch_semantic_integrate

from .ner.extractor import ConceptExtractor
# from .ner.prompts import ... (prompts usually used internally)

from .enrichment.translation import baidu_translate_text
from .enrichment.wikipedia_api import WikipediaService
# from .enrichment.conceptnet_api import ...
# from .enrichment.explanation_generator import ExplanationGenerator

from .multimodal.pdf_processing import extract_images_from_pdf # Assuming this function name
# from .multimodal.image_analysis import ImageConceptAligner
# from .multimodal.speech_synthesis import TextToSpeechSynthesizer

# from .structuring.json_operations import ...
# from .triplestore.triple_generator import ...

# Potentially a high-level orchestrator class
# from .main_orchestrator import PipelineOrchestrator

print("Educational Content Pipeline library initialized.")
# You can also perform one-time setup here if necessary, like calling config.setup_proxies()
# though it's already called when config.py is imported.