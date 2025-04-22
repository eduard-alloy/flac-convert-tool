#!/usr/bin/env python3
"""
Metadata parsing functions for FLAC converter.
Handles finding and parsing album info, track info, and cover art.
"""

import os
import re
import logging

# Set up logging
logger = logging.getLogger(__name__)

def find_album_info(directory):
    """Find and parse album info files in the directory."""
    album_info = {}
    
    # Look for AlbumInfo.txt files
    for root, _, files in os.walk(directory):
        for file in files:
            if file == 'AlbumInfo.txt':
                album_path = os.path.join(root, file)
                try:
                    with open(album_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                        
                    # Parse basic album info using simpler regex patterns
                    album_data = {}
                    
                    # Use safer pattern matching
                    id_match = re.search(r'\[ID\][ \t]*(.*?)[\r\n]', content)
                    title_match = re.search(r'\[Title\][ \t]*(.*?)[\r\n]', content)
                    artist_match = re.search(r'\[Artists\][ \t]*(.*?)[\r\n]', content)
                    release_match = re.search(r'\[ReleaseDate\][ \t]*(.*?)[\r\n]', content)
                    tracks_match = re.search(r'\[SongNum\][ \t]*(.*?)[\r\n]', content)
                    duration_match = re.search(r'\[Duration\][ \t]*(.*?)[\r\n]', content)
                    
                    album_data['id'] = id_match.group(1).strip() if id_match else None
                    album_data['title'] = title_match.group(1).strip() if title_match else None
                    album_data['artist'] = artist_match.group(1).strip() if artist_match else None
                    album_data['release_date'] = release_match.group(1).strip() if release_match else None
                    album_data['track_count'] = tracks_match.group(1).strip() if tracks_match else None
                    album_data['duration'] = duration_match.group(1).strip() if duration_match else None
                    
                    # Parse track listings with simpler pattern
                    tracks = {}
                    track_matches = re.findall(r'\[(\d+)\][ \t]*(.*?)[\r\n]', content)
                    for track_num, track_title in track_matches:
                        tracks[track_num] = track_title.strip()
                    
                    album_data['tracks'] = tracks
                    album_info[os.path.dirname(album_path)] = album_data
                    
                    logger.info(f"Found album info: {album_data.get('title', 'Unknown')} by {album_data.get('artist', 'Unknown')}")
                except Exception as e:
                    logger.error(f"Error parsing album info file {album_path}: {str(e)}")
    
    return album_info

def find_track_info_files(directory):
    """Find all track info files in the directory."""
    track_info_files = {}
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.info'):
                # Associate the info file with the corresponding flac file
                base_name = os.path.splitext(file)[0]
                flac_file = None
                
                # Check if there's a matching flac file
                for potential_match in os.listdir(root):
                    if potential_match.endswith('.flac') and base_name.split(' - ')[-1] in potential_match:
                        flac_file = os.path.join(root, potential_match)
                        break
                
                if flac_file:
                    track_info_files[flac_file] = os.path.join(root, file)
    
    return track_info_files

def parse_track_info(info_file):
    """Parse track info file to extract metadata."""
    try:
        with open(info_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Extract metadata
        metadata = {}
        
        # Basic metadata fields to extract
        fields = {
            'title': r'Title: (.*?)$',
            'album': r'Album: (.*?)$',
            'artist': r'Artist: (.*?)$',
            'album_artist': r'Album Artist: (.*?)$',
            'copyright': r'Copyright: (.*?)$',
            'track_number': r'Track Number: (.*?)$',
            'total_tracks': r'Total Tracks: (.*?)$',
            'disc_number': r'Disc Number: (.*?)$',
            'total_discs': r'Total Discs: (.*?)$',
            'isrc': r'ISRC: (.*?)$',
            'release_date': r'Release Date: (.*?)$',
            'audio_quality': r'Audio Quality: (.*?)$',
            'composer': r'Composer: (.*?)$'
        }
        
        for key, pattern in fields.items():
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                metadata[key] = match.group(1).strip()
        
        # Extract lyrics if present
        lyrics_section = re.search(r'# Lyrics\n(.*?)(?=\n\n|\Z)', content, re.DOTALL | re.MULTILINE)
        if lyrics_section:
            lyrics_text = lyrics_section.group(1).strip()
            # Parse timestamped lyrics
            lyrics_lines = []
            for line in lyrics_text.split('\n'):
                if line.strip():
                    lyrics_lines.append(line)
            
            if lyrics_lines:
                metadata['lyrics'] = '\n'.join(lyrics_lines)
        
        return metadata
    except Exception as e:
        logger.error(f"Error parsing track info file {info_file}: {str(e)}")
        return {}

def find_cover_art(directory):
    """Find album cover art files in the directory."""
    cover_files = {}
    
    # Common cover art filenames
    cover_patterns = [
        'cover', 'folder', 'album', 'front', 'artwork', 'albumart'
    ]
    
    for root, _, files in os.walk(directory):
        potential_covers = []
        
        # First check for standard naming patterns
        for file in files:
            base_name = os.path.splitext(file.lower())[0]
            ext = os.path.splitext(file.lower())[1]
            
            if ext in ['.jpg', '.jpeg', '.png'] and any(pattern in base_name for pattern in cover_patterns):
                potential_covers.append(os.path.join(root, file))
                
        # If no standard cover found, check for any image file
        if not potential_covers:
            for file in files:
                ext = os.path.splitext(file.lower())[1]
                if ext in ['.jpg', '.jpeg', '.png']:
                    potential_covers.append(os.path.join(root, file))
        
        # Use the first found cover art for this directory
        if potential_covers:
            cover_files[root] = potential_covers[0]
            logger.info(f"Found cover art: {potential_covers[0]}")
    
    return cover_files
