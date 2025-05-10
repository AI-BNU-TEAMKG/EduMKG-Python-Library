import os
import shutil
import json
from typing import List, Any, Dict

def get_filenames_recursive(directory: str, extension: str) -> List[str]:
    """
    Recursively finds all files with a given extension in a directory.
    """
    files_found = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith(extension):
                files_found.append(os.path.join(root, filename))
    return files_found

def remove_blank_lines_from_txt(file_path: str) -> None:
    """
    Removes blank lines from a text file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        with open(file_path, 'w', encoding='utf-8') as file:
            for line in lines:
                if line.strip():  # Only write non-blank lines
                    file.write(line)
        
        print(f"Blank lines removed from {file_path}")
    
    except Exception as e:
        print(f"Error removing blank lines from {file_path}: {e}")

def read_json_file(file_path: str) -> Any:
    """Reads data from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        return None

def write_json_file(data: Any, file_path: str, indent: int = 4) -> None:
    """Writes data to a JSON file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        print(f"Data successfully written to {file_path}")
    except Exception as e:
        print(f"Error writing JSON to {file_path}: {e}")

def ensure_directory_exists(file_path: str) -> None:
    """Ensures the directory for a given file_path exists."""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def safe_filename_segment(text: str, max_length: int = 20) -> str:
    """
    Creates a safe filename segment from text, keeping only Chinese characters
    and limiting length.
    """
    safe_text = ''.join(c for c in text if '\u4e00' <= c <= '\u9fff')
    return safe_text[:max_length]