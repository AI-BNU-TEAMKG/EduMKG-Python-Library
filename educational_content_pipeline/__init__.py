# educational_content_pipeline/__init__.py

# Expose key classes or functions from submodules
from .utils.file_operations import get_filenames_recursive, read_json_file, write_json_file
from .utils.api_client import llm_client, LLMClient

from .dataprocess.audio_video import process_mp4_to_mp3_conversion, process_video_clipping
from .dataprocess.text_extraction import process_docx_to_timestamped_text
from .dataprocess.llm_segmentation import semantic_integrate_text_file, batch_semantic_integrate

from .ner.extractor import ConceptExtractor


from .enrichment.translation import baidu_translate_text
from .enrichment.wikipedia_api import WikipediaService


from .multimodal.pdf_processing import extract_images_from_pdf # Assuming this function name


print("Educational Content Pipeline library initialized.")
