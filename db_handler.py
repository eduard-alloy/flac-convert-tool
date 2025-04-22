#!/usr/bin/env python3
"""
Database handling functions for FLAC converter.
Handles reading the JSON database and tracking converted files.
"""

import os
import json
import logging
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

def read_database(db_file, base_dir=None, artist_filter=None, album_id_filter=None, year_filter=None):
    """Read the JSON database file and filter by criteria if provided."""
    try:
        with open(db_file, 'r', encoding='utf-8') as f:
            database = json.load(f)
        
        # If base_dir is not provided, use the directory containing the db file
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(db_file))
            logger.info(f"Using database directory as base directory: {base_dir}")
        
        logger.info(f"Successfully loaded database from {db_file} with {len(database)} entries")
        
        # Apply filters
        filtered_albums = {}
        
        # Handle multiple artists if provided
        artists_to_filter = []
        if artist_filter:
            if ',' in artist_filter:
                # Split comma-separated artists
                artists_to_filter = [a.strip().lower() for a in artist_filter.split(',')]
                logger.info(f"Filtering by multiple artists: {artists_to_filter}")
            else:
                artists_to_filter = [artist_filter.lower()]
                logger.info(f"Filtering by artist: {artist_filter}")
        
        for album_id, album_data in database.items():
            # Skip entries that don't match filters
            
            # Artist filter - check if any artist matches any of the specified filters
            if artists_to_filter and not any(
                    any(filter_artist in artist.lower() for artist in album_data.get('artists', []))
                    for filter_artist in artists_to_filter
                ):
                continue
                
            # Album ID filter
            if album_id_filter and album_id != album_id_filter:
                continue
                
            # Year filter
            if year_filter and album_data.get('year') != year_filter:
                continue
            
            # Add to filtered results
            filtered_albums[album_id] = album_data
        
        # Process paths to be absolute and sanitized
        for album_id, album_data in filtered_albums.items():
            path = album_data.get('path', '')
            
            # Remove # prefix if present (seems to be a marker in your database)
            if path.startswith('#/'):
                path = path[2:]
                
            # Prepend base_dir if provided and ensure proper path joining
            if base_dir:
                # Use Path for proper cross-platform path handling
                path = os.path.normpath(os.path.join(base_dir, path))
            
            album_data['absolute_path'] = path
            
            # Log any paths with special characters that might cause issues
            if '(' in path or ')' in path:
                logger.debug(f"Album path contains parentheses: {path}")
        
        logger.info(f"After filtering: {len(filtered_albums)} albums")
        
        # Print all filtered albums for debugging
        for album_id, album_data in filtered_albums.items():
            logger.debug(f"Album {album_id}: {album_data.get('title', 'Unknown')} - {album_data.get('absolute_path', 'No path')}")
        
        return filtered_albums
    
    except Exception as e:
        logger.error(f"Error reading database file {db_file}: {str(e)}")
        return {}

def load_conversion_tracking(tracking_file):
    """Load the list of already converted files."""
    if os.path.exists(tracking_file):
        try:
            with open(tracking_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading tracking file {tracking_file}: {str(e)}")
            return {}
    return {}

def update_conversion_tracking(tracking_file, flac_file, output_file, album_id=None):
    """Update the tracking file with a newly converted file."""
    tracking_data = load_conversion_tracking(tracking_file)
    
    # Create a unique key for the file
    key = flac_file
    
    # Add or update the entry
    tracking_data[key] = {
        'output_file': output_file,
        'album_id': album_id,
        'converted_at': Path(output_file).stat().st_mtime if os.path.exists(output_file) else 0
    }
    
    # Save the updated tracking data
    try:
        with open(tracking_file, 'w', encoding='utf-8') as f:
            json.dump(tracking_data, f, indent=2)
    except Exception as e:
        logger.error(f"Error updating tracking file {tracking_file}: {str(e)}")
