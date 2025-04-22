#!/usr/bin/env python3
"""
File conversion functions for FLAC converter.
Handles converting FLAC files to other formats.
"""

import os
import subprocess
import logging
from pathlib import Path
import shutil

# Import from other modules
from db_handler import update_conversion_tracking, load_conversion_tracking
from metadata_parser import parse_track_info
from metadata_writer import apply_metadata

# Set up logging
logger = logging.getLogger(__name__)

# Import the FLAC level detection module if available
try:
    from flac_level_detection import get_flac_compression_level
    has_flac_detection = True
except ImportError:
    logger.info("FLAC level detection module not available")
    has_flac_detection = False

def create_output_dir_structure(input_dir, output_dir, flac_file):
    """Create the corresponding output directory structure."""
    rel_path = os.path.relpath(os.path.dirname(flac_file), input_dir)
    output_path = os.path.join(output_dir, rel_path)
    os.makedirs(output_path, exist_ok=True)
    return output_path

def should_convert(flac_file, output_file, tracking_file, force=False):
    """Check if a file should be converted based on tracking data."""
    # If force conversion, always return True
    if force:
        return True
        
    # If output file doesn't exist, convert
    if not os.path.exists(output_file):
        return True
    
    # Check tracking data
    tracking_data = load_conversion_tracking(tracking_file)
    
    # If not in tracking data, convert
    if flac_file not in tracking_data:
        return True
    
    # Check if output file has been modified since tracking
    if os.path.exists(output_file):
        current_mtime = Path(output_file).stat().st_mtime
        tracked_mtime = tracking_data[flac_file].get('converted_at', 0)
        
        # If modification times don't match, convert
        if current_mtime != tracked_mtime:
            return True
    
    # If we get here, the file is already converted and up to date
    return False


def convert_file(args):
    """Convert a FLAC file to the specified format and embed metadata."""
    # Handle variable number of arguments
    if len(args) > 12:
        flac_file_info, input_dir, output_dir, output_format, bitrate, album_info, track_info_files, cover_files, tracking_file, force, skip_metadata, lyrics_mode, compression_level = args
    else:
        flac_file_info, input_dir, output_dir, output_format, bitrate, album_info, track_info_files, cover_files, tracking_file, force, skip_metadata, lyrics_mode = args
        compression_level = 5  # Default value if not provided
    
    # Unpack the flac_file_info tuple
    flac_file, album_id = flac_file_info
    
    # Create output directory structure mirroring the input
    output_path = create_output_dir_structure(input_dir, output_dir, flac_file)
    
    # Build output filename
    input_filename = os.path.basename(flac_file)
    output_filename = os.path.splitext(input_filename)[0] + f'.{output_format}'
    output_file = os.path.join(output_path, output_filename)
    
    # Check if we should convert this file
    if not should_convert(flac_file, output_file, tracking_file, force):
        logger.info(f"Skipping already converted file: {output_file}")
        return True, output_file
    
    # Special case: if output format is also FLAC, we can optimize by copying or recompressing
    if output_format == 'flac':
        return convert_to_flac(flac_file, output_file, compression_level, album_info, track_info_files, cover_files, 
                         tracking_file, skip_metadata, lyrics_mode, album_id)
        
    # Build ffmpeg command for other formats
    cmd = [
        'ffmpeg',
        '-i', flac_file,
        '-y',  # Overwrite output file if it exists
        '-v', 'error',  # Only show errors
        '-map_metadata', '0',  # Copy metadata from input
    ]
    
    # Add format-specific options
    if output_format == 'mp3':
        cmd.extend(['-codec:a', 'libmp3lame', '-q:a', '0', '-b:a', bitrate, '-id3v2_version', '3'])
    elif output_format == 'ogg':
        cmd.extend(['-codec:a', 'libvorbis', '-q:a', '10'])
    elif output_format == 'opus':
        cmd.extend(['-codec:a', 'libopus', '-b:a', bitrate])
    elif output_format == 'aac':
        cmd.extend(['-codec:a', 'aac', '-b:a', bitrate, '-strict', 'experimental'])
    elif output_format == 'm4a':
        cmd.extend(['-codec:a', 'aac', '-b:a', bitrate, '-f', 'mp4'])
    
    # Add output file to command
    cmd.append(output_file)
    
    try:
        # Run the conversion
        process = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Now enhance the metadata using track info files and album info
        if not skip_metadata:
            try:
                # Get album directory for this track
                album_dir = os.path.dirname(flac_file)
                
                # Get track info if available
                track_metadata = {}
                if flac_file in track_info_files:
                    track_info_file = track_info_files[flac_file]
                    track_metadata = parse_track_info(track_info_file)
                    logger.debug(f"Found track info for {os.path.basename(flac_file)}")
                
                # Get album info if available
                album_metadata = {}
                if album_dir in album_info:
                    album_metadata = album_info[album_dir]
                    logger.debug(f"Found album info for {os.path.basename(flac_file)}")
                
                # Get cover art if available
                cover_art = None
                if album_dir in cover_files:
                    cover_art = cover_files[album_dir]
                    logger.debug(f"Found cover art for {os.path.basename(flac_file)}")
                
                # Apply metadata using the metadata writer module
                if apply_metadata(output_file, output_format, track_metadata, album_metadata, cover_art, lyrics_mode):
                    logger.info(f"Enhanced metadata for {os.path.basename(output_file)}")
                
            except Exception as e:
                logger.error(f"Error enhancing metadata for {output_file}: {str(e)}")
        
        # Update tracking information
        update_conversion_tracking(tracking_file, flac_file, output_file, album_id)
            
        return True, output_file
    except subprocess.CalledProcessError as e:
        logger.error(f"Error converting {flac_file}: {e.stderr.decode().strip()}")
        return False, flac_file

def convert_to_flac(flac_file, output_file, compression_level, album_info, track_info_files, 
                   cover_files, tracking_file, skip_metadata, lyrics_mode, album_id, input_compression_level=None):
    """Handle FLAC to FLAC conversion (copy or recompress)."""
    try:
        # If input compression level is known and matches target, just copy the file
        if input_compression_level is not None and input_compression_level == compression_level:
            # Use a simple file copy operation for speed
            shutil.copy2(flac_file, output_file)
            logger.info(f"Copied FLAC file with matching compression level ({compression_level}): {os.path.basename(output_file)}")
        elif compression_level == 5:  # Default compression, we'll copy unless we know input is different
            if input_compression_level is not None and input_compression_level != 5:
                # Re-encode with the default compression level
                cmd = [
                    'ffmpeg',
                    '-i', flac_file,
                    '-y',  # Overwrite output file if it exists
                    '-v', 'error',  # Only show errors
                    '-map_metadata', '0',  # Copy metadata from input
                    '-codec:a', 'flac',
                    '-compression_level', str(compression_level),
                    output_file
                ]
                
                process = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                logger.info(f"Re-compressed FLAC file to level {compression_level}: {os.path.basename(output_file)}")
            else:
                # Just copy the file if we don't know the input level or it's also 5
                shutil.copy2(flac_file, output_file)
                logger.info(f"Copied FLAC file (using default level {compression_level}): {os.path.basename(output_file)}")
        else:
            # Re-encode with the specified compression level
            cmd = [
                'ffmpeg',
                '-i', flac_file,
                '-y',  # Overwrite output file if it exists
                '-v', 'error',  # Only show errors
                '-map_metadata', '0',  # Copy metadata from input
                '-codec:a', 'flac',
                '-compression_level', str(compression_level),
                output_file
            ]
            
            process = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"Re-compressed FLAC file with level {compression_level}: {os.path.basename(output_file)}")
        
        # Apply metadata if needed (usually not needed for FLAC to FLAC, but just in case)
        if not skip_metadata:
            album_dir = os.path.dirname(flac_file)
            
            track_metadata = {}
            if flac_file in track_info_files:
                track_info_file = track_info_files[flac_file]
                track_metadata = parse_track_info(track_info_file)
            
            album_metadata = {}
            if album_dir in album_info:
                album_metadata = album_info[album_dir]
            
            cover_art = None
            if album_dir in cover_files:
                cover_art = cover_files[album_dir]
            
            if apply_metadata(output_file, 'flac', track_metadata, album_metadata, cover_art, lyrics_mode):
                logger.info(f"Enhanced metadata for {os.path.basename(output_file)}")
        
        # Update tracking information
        update_conversion_tracking(tracking_file, flac_file, output_file, album_id)
        return True, output_file
    
    except Exception as e:
        logger.error(f"Error in FLAC to FLAC conversion for {flac_file}: {str(e)}")
        return False, flac_file
