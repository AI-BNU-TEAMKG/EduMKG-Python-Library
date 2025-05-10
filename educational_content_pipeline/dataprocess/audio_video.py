import os
import re
from moviepy.editor import VideoFileClip
from typing import Dict, Tuple, List
from ..utils.file_operations import ensure_directory_exists, safe_filename_segment

def convert_mp4_to_mp3(input_file: str, output_file: str) -> bool:
    """Converts an MP4 video file to MP3 audio."""
    try:
        ensure_directory_exists(output_file)
        video = VideoFileClip(input_file)
        video.audio.write_audiofile(output_file)
        video.close()
        print(f"Successfully converted {input_file} to {output_file}")
        return True
    except Exception as e:
        print(f"Error converting {input_file} to MP3: {e}")
        return False

def process_mp4_to_mp3_conversion(mp4_path: str) -> Optional[str]:
    """
    Processes a single MP4 file, converting it to MP3.
    Handles existing output filenames by appending a counter.
    Returns the path to the generated MP3 file or None on failure.
    """
    file_prefix = os.path.splitext(os.path.basename(mp4_path))[0]
    output_dir = os.path.dirname(mp4_path)
    output_path = os.path.join(output_dir, f"{file_prefix}.mp3")

    counter = 1
    while os.path.exists(output_path):
        output_path = os.path.join(output_dir, f"{file_prefix}_{counter}.mp3")
        counter += 1
    
    print(f"Attempting to convert {mp4_path} to {output_path}")
    if convert_mp4_to_mp3(mp4_path, output_path):
        return output_path
    return None


def parse_timestamped_text_file(text_file_path: str) -> Dict[str, Tuple[int, int, str]]:
    """
    Parses a text file with lines like '"MM:SS-MM:SS": "description"'
    Returns a dictionary: {"clip_START_END": (start_sec, end_sec, description)}
    """
    timestamps_data = {}
    try:
        with open(text_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading timestamp file {text_file_path}: {e}")
        return timestamps_data

    pattern = r'"(\d{2}:\d{2}-\d{2}:\d{2})"\s*:\s*"([^"]*)"'
    matches = re.findall(pattern, content)
    
    def time_to_seconds(time_str: str) -> int:
        mins, secs = map(int, time_str.split(':'))
        return mins * 60 + secs

    for timestamp_range, description in matches:
        start_str, end_str = timestamp_range.split('-')
        start_sec = time_to_seconds(start_str)
        end_sec = time_to_seconds(end_str)
        
        key = f"clip_{start_str.replace(':', '_')}" # e.g., clip_00_15
        timestamps_data[key] = (start_sec, end_sec, description)
    
    return timestamps_data


def trim_video_by_timestamps(input_video_path: str, output_base_name: str,
                             timestamps_data: Dict[str, Tuple[int, int, str]],
                             output_clips_subdir: Optional[str] = None) -> List[str]:
    """
    Trims an input video into multiple clips based on provided timestamps.

    Args:
        input_video_path: Path to the source video file.
        output_base_name: Base for naming output clips (often video name without ext).
        timestamps_data: Dictionary from parse_timestamped_text_file.
        output_clips_subdir: Optional subdirectory name to save clips. If None,
                             a subdir named after the input video's parent folder is used.

    Returns:
        A list of paths to the generated video clips.
    """
    created_clips = []
    try:
        video = VideoFileClip(input_video_path)
    except Exception as e:
        print(f"Error opening video file {input_video_path}: {e}")
        return created_clips

    if output_clips_subdir:
        clips_output_folder = os.path.join(os.path.dirname(input_video_path), output_clips_subdir)
    else:
        # Original logic: create a subdir named after the video's containing folder
        input_folder_name = os.path.basename(os.path.dirname(input_video_path))
        if not input_folder_name: # If video is in root processing dir
            input_folder_name = os.path.splitext(os.path.basename(input_video_path))[0] + "_clips"
        clips_output_folder = os.path.join(os.path.dirname(input_video_path), input_folder_name)
    
    os.makedirs(clips_output_folder, exist_ok=True)

    for clip_name_prefix, (start_sec, end_sec, content) in timestamps_data.items():
        try:
            # Sanitize content for filename
            safe_content_suffix = safe_filename_segment(content)
            output_filename = os.path.join(clips_output_folder, f"{clip_name_prefix}_{safe_content_suffix}.mp4")
            
            # Ensure end_sec is not beyond video duration
            if end_sec > video.duration:
                print(f"Warning: Clip {clip_name_prefix} end time {end_sec}s exceeds video duration {video.duration}s. Adjusting to video end.")
                end_sec = video.duration
            if start_sec >= end_sec:
                print(f"Warning: Clip {clip_name_prefix} start time {start_sec}s is not before end time {end_sec}s. Skipping.")
                continue

            clip = video.subclip(start_sec, end_sec)
            clip.write_videofile(output_filename, codec='libx264', audio_codec='aac', logger=None) # logger=None to suppress moviepy prints
            clip.close()
            
            print(f"Successfully created clip: {output_filename} ({start_sec}s - {end_sec}s)")
            created_clips.append(output_filename)
        
        except Exception as e:
            print(f"Error creating clip {clip_name_prefix} ({start_sec}s - {end_sec}s): {e}")
    
    video.close()
    return created_clips

def process_video_clipping(video_path: str, timestamp_txt_path: Optional[str] = None) -> List[str]:
    """
    Orchestrates parsing timestamps and clipping a video.
    If timestamp_txt_path is None, it will try to find a corresponding .txt file.
    The convention for timestamp file is VideoName_.txt in the same directory as video, or in parent dir.
    Example: for video 'folder/video1.mp4', it might look for
             'folder/video1_.txt' or 'folder/folder_.txt' (original logic was complex).
             Let's simplify: look for 'video_name_.txt' in same dir, then parent dir.
    """
    if timestamp_txt_path is None:
        base_video_name = os.path.splitext(os.path.basename(video_path))[0]
        video_dir = os.path.dirname(video_path)
        
        # Try `video_name_.txt` in the same directory
        candidate_ts_path = os.path.join(video_dir, f"{base_video_name}_.txt")
        if not os.path.exists(candidate_ts_path):
            # Try `parent_folder_name_.txt` in the parent directory (original logic)
            # This path was: '\\'.join(input_file.split('\\')[:-1]) + '\\' + '\\'.join(input_file.split('\\')[-2:-1])+ '_.txt'
            # Which translates to: os.path.join(os.path.dirname(video_dir), os.path.basename(video_dir) + "_.txt")
            parent_dir = os.path.dirname(video_dir)
            parent_folder_name = os.path.basename(video_dir)
            candidate_ts_path = os.path.join(parent_dir, f"{parent_folder_name}_.txt")
            if not os.path.exists(candidate_ts_path):
                 print(f"Timestamp file not found for {video_path} using default patterns.")
                 return []
        timestamp_txt_path = candidate_ts_path
        print(f"Using timestamp file: {timestamp_txt_path}")


    timestamps_data = parse_timestamped_text_file(timestamp_txt_path)
    if not timestamps_data:
        print(f"No timestamps found or error parsing {timestamp_txt_path} for video {video_path}.")
        return []

    output_base_name = os.path.splitext(os.path.basename(video_path))[0]
    return trim_video_by_timestamps(video_path, output_base_name, timestamps_data)