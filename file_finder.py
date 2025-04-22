#!/usr/bin/env python3
"""
File finding functions for FLAC converter.
Handles finding FLAC files from directories or database entries.
"""

import os
import logging
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

def find_flac_files(input_dir):
    """Recursively find all FLAC files in the input directory."""
    flac_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith('.flac'):
                flac_files.append((os.path.join(root, file), None))  # None for album_id to match db format
    return flac_files

def find_flac_files_from_db(albums, base_dir=None):
    """Find FLAC files based on album paths from the database."""
    flac_files = []
    missing_album_paths = []
    
    for album_id, album_data in albums.items():
        album_path = album_data.get('absolute_path')
        if not album_path:
            logger.warning(f"Album missing path: {album_data.get('title', 'Unknown')}")
            continue
            
        # Ensure the path exists
        if not os.path.exists(album_path):
            logger.warning(f"Album path does not exist: {album_path}")
            missing_album_paths.append((album_id, album_data))
            continue
        
        # Try to find FLAC files
        album_flac_files = []
        for root, _, files in os.walk(album_path):
            for file in files:
                if file.lower().endswith('.flac'):
                    flac_file_path = os.path.join(root, file)
                    # Add album ID to the file info for later reference
                    album_flac_files.append((flac_file_path, album_id))
        
        # Report if no FLAC files found in an existing directory
        if not album_flac_files:
            logger.warning(f"No FLAC files found in album path: {album_path}")
        else:
            logger.info(f"Found {len(album_flac_files)} FLAC files in album: {album_data.get('title', 'Unknown')}")
            flac_files.extend(album_flac_files)
    
    # If paths are missing, try to do fuzzy matching to find them
    if missing_album_paths and base_dir:
        for album_id, album_data in missing_album_paths:
            title = album_data.get('title', '').lower()
            found_flacs = find_album_with_fuzzy_matching(base_dir, title, album_id)
            if found_flacs:
                flac_files.extend(found_flacs)
    
    return flac_files

def find_album_with_fuzzy_matching(base_dir, album_title, album_id):
    """Try to find an album using fuzzy directory matching."""
    found_flacs = []
    
    # Convert album title to lowercase for comparison
    album_title = album_title.lower()
    
    # Walk through the base directory to find potential matches
    for root, dirs, _ in os.walk(base_dir):
        for dir_name in dirs:
            # Check if directory name contains the album title
            if album_title in dir_name.lower():
                potential_path = os.path.join(root, dir_name)
                logger.info(f"Potential album match found for '{album_title}': {potential_path}")
                
                # Look for FLAC files in this directory
                for sub_root, _, files in os.walk(potential_path):
                    for file in files:
                        if file.lower().endswith('.flac'):
                            flac_file_path = os.path.join(sub_root, file)
                            found_flacs.append((flac_file_path, album_id))
                
                if found_flacs:
                    logger.info(f"Found {len(found_flacs)} FLAC files in potential match directory: {potential_path}")
                    return found_flacs
    
    logger.warning(f"No fuzzy matches found for album: {album_title}")
    return []

def sanitize_path(path):
    """Sanitize a path to handle special characters and spaces."""
    # Convert to Path object for safer handling
    return str(Path(path))
