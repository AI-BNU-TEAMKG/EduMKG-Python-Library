import docx
import os
from typing import List, Dict, Optional
from ..utils.file_operations import ensure_directory_exists

def extract_time_coded_content_from_docx(docx_file_path: str) -> List[str]:
    """
    Extracts time-coded content from a DOCX file.
    Assumes a specific format: "发言人 HH:MM:SS" followed by content.
    Returns a list of strings, each "START_TIME-END_TIME: content".
    """
    try:
        doc = docx.Document(docx_file_path)
    except Exception as e:
        print(f"Error opening DOCX file {docx_file_path}: {e}")
        return []

    full_text = '\n'.join([para.text for para in doc.paragraphs])
    lines = full_text.split('\n')
    
    time_coded_content: Dict[str, str] = {}
    current_time_code: Optional[str] = None
    current_content_lines: List[str] = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith('发言人') and ' ' in line:
            parts = line.split()
            if len(parts) > 1 and re.match(r'\d{2}:\d{2}:\d{2}', parts[1]): # Check if second part is a time code
                if current_time_code:
                    time_coded_content[current_time_code] = ' '.join(current_content_lines).strip()
                
                current_time_code = parts[1] # HH:MM:SS
                current_content_lines = []
                # If there's content on the same line after time code
                if len(parts) > 2:
                    current_content_lines.append(' '.join(parts[2:]))
            else: # Not a valid speaker line, treat as content
                 if current_time_code:
                    current_content_lines.append(line)
        elif current_time_code:
            current_content_lines.append(line)
    
    if current_time_code and current_content_lines: # Capture the last segment
        time_coded_content[current_time_code] = ' '.join(current_content_lines).strip()

    # Format output with start and end times
    formatted_output: List[str] = []
    
    # Sort time codes (HH:MM:SS format allows string sort)
    sorted_time_codes = sorted(list(time_coded_content.keys()))
    
    for i in range(len(sorted_time_codes)):
        start_time = sorted_time_codes[i]
        content = time_coded_content[start_time]
        
        if i + 1 < len(sorted_time_codes):
            end_time_full = sorted_time_codes[i+1]
            formatted_output.append(f"{start_time}-{end_time}: {content}")
        else:

            pass # Original logic implicitly skips the last segment for ranged output

    return formatted_output


def process_docx_to_timestamped_text(docx_file_path: str, output_txt_path: Optional[str] = None) -> Optional[str]:
    """
    Extracts timestamped conversations from a DOCX file and writes them to a TXT file.
    Output format in TXT: "START_TIME-END_TIME": "content"
    Returns the path to the output TXT file or None on failure.
    """
    if output_txt_path is None:
        output_txt_path = docx_file_path.replace('_原文.docx', '.txt').replace('.docx', '.txt')
    
    ensure_directory_exists(output_txt_path)

    try:
        results = extract_time_coded_content_from_docx(docx_file_path)
        if not results:
            print(f"No time-coded content found in {docx_file_path}")
            return None

        with open(output_txt_path, 'w', encoding='utf-8') as f:
            for result_line in results:
                try:
                    time_range, content = result_line.split(': ', 1)
                    # Ensure quotes are properly escaped if content itself has quotes
                    # For simplicity here, assuming content doesn't break JSON-like format
                    f.write(f'"{time_range}": "{content.replace("\"", "\\\"")}"\n')
                except ValueError:
                    print(f"Warning: Could not parse line for output: {result_line}")
        
        print(f"Timestamped conversation extracted to {output_txt_path}")
        return output_txt_path
    
    except Exception as e:
        print(f"An error occurred during DOCX to TXT processing for {docx_file_path}: {e}")
        return None
