import os
from typing import List, Optional
from ..utils.file_operations import ensure_directory_exists
from ..utils.api_client import llm_client # Using the new client
from .. import config


_LLM_CALL_COUNT = 0 

def semantic_integrate_text_file(
    input_txt_path: str, 
    output_txt_path: Optional[str] = None,
    max_calls: int = config.LLM_SEMANTIC_INTEGRATION_MAX_CALLS
    ) -> Optional[str]:
    """
    Uses an LLM (Gemini) to re-segment content in a text file based on semantics.
    Input file format: lines of text.
    Output file format: LLM's response (expected: "timestamp":"content" lines).

    Args:
        input_txt_path: Path to the input text file.
        output_txt_path: Path for the output. If None, derived from input name (_
        .txt).
        max_calls: Maximum number of LLM calls allowed for this operation globally (approximate).

    Returns:
        Path to the output file if successful, else None.
    """
    global _LLM_CALL_COUNT
    
    if output_txt_path is None:
        output_txt_path = input_txt_path.replace(".txt", "_.txt")

    ensure_directory_exists(output_txt_path)

    try:
        with open(input_txt_path, 'r', encoding='utf-8') as f:
            content_to_segment = f.read()
    except Exception as e:
        print(f"Error reading input file {input_txt_path} for segmentation: {e}")
        return None

    if not content_to_segment.strip():
        print(f"Input file {input_txt_path} is empty. Skipping segmentation.")
        # Optionally create an empty output file or return None
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write("") # Create empty output
        return output_txt_path


    if _LLM_CALL_COUNT >= max_calls:
        print(f"LLM call limit ({max_calls}) reached. Skipping segmentation for {input_txt_path}.")
        return None # Or indicate that limit was reason for not processing

    prompt = (
        "现在需要你将下面的音频段落按照语义重新分段，"
        "输出格式为“时间戳”:“内容”，"
        "“内容不需要你总结，你只负责按照新的时间戳合并原文内容”："
        f"{content_to_segment}"
    )
    
    # Using the centralized LLM client
    # Assuming Gemini is configured and API key is available via config
    response_text = llm_client.call_google_gemini(
        model_name=config.DEFAULT_GEMINI_MODEL,
        content=prompt
    )
    _LLM_CALL_COUNT += 1

    if response_text:
        try:
            with open(output_txt_path, 'w', encoding='utf-8') as f:
                f.write(response_text)
            print(f"Semantic segmentation for {input_txt_path} written to {output_txt_path}")
            return output_txt_path
        except Exception as e:
            print(f"Error writing segmented output to {output_txt_path}: {e}")
            return None
    else:
        print(f"LLM failed to provide segmentation for {input_txt_path}.")
        return None

def batch_semantic_integrate(txt_file_paths: List[str]) -> List[str]:
    """Processes a list of text files for semantic integration."""
    # Note: _LLM_CALL_COUNT is global here. For true library use,
    # this counter might need to be managed by a class instance or passed around.
    processed_files = []
    for file_path in txt_file_paths:
        output_file = semantic_integrate_text_file(file_path)
        if output_file:
            processed_files.append(output_file)
    return processed_files
