#!/usr/bin/env python3
"""
Helper module to analyze FLAC files and determine their compression level
for integration with the main FLAC converter.
"""

import os
import subprocess
import logging
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

def analyze_flac_file(flac_file):
    """Analyze a FLAC file and extract technical information."""
    if not os.path.exists(flac_file):
        logger.error(f"File not found: {flac_file}")
        return None
        
    # Get file size
    file_size = os.path.getsize(flac_file)
    
    try:
        # First, check if the flac and metaflac tools are available
        try:
            subprocess.run(['flac', '--version'], capture_output=True, check=True)
            subprocess.run(['metaflac', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("FLAC command-line tools not available. Limited analysis possible.")
            # Return basic info without full analysis
            return {
                'file_size': file_size,
                'limited_analysis': True
            }
            
        # Run flac command line tool with analysis flags
        flac_info = subprocess.run(
            ['flac', '--analyze', '--show-format', '--show-streaminfo', flac_file],
            capture_output=True, text=True, check=True
        )
        
        # Run metaflac to get audio statistics
        metaflac_info = subprocess.run(
            ['metaflac', '--show-min-blocksize', '--show-max-blocksize', 
             '--show-min-framesize', '--show-max-framesize', flac_file],
            capture_output=True, text=True, check=True
        )
        
        # Parse information from output
        info = {}
        info['file_size'] = file_size
        
        # Parse basic info from flac output
        for line in flac_info.stdout.splitlines():
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                info[key] = value
        
        # Parse blocksize info from metaflac
        lines = metaflac_info.stdout.splitlines()
        if len(lines) >= 4:
            info['min_blocksize'] = int(lines[0].strip())
            info['max_blocksize'] = int(lines[1].strip())
            info['min_framesize'] = int(lines[2].strip())
            info['max_framesize'] = int(lines[3].strip())
        
        # Calculate derived statistics
        if 'sample_rate' in info and 'channels' in info and 'bits_per_sample' in info:
            info['sample_rate'] = int(info['sample_rate'])
            info['channels'] = int(info['channels'])
            info['bits_per_sample'] = int(info['bits_per_sample'])
            
            # Calculate theoretical uncompressed size
            duration_seconds = float(info.get('duration', '0').replace(' s', ''))
            uncompressed_bytes = int(duration_seconds * info['sample_rate'] * info['channels'] * (info['bits_per_sample'] / 8))
            info['uncompressed_size'] = uncompressed_bytes
            
            # Calculate compression ratio
            if uncompressed_bytes > 0:
                info['compression_ratio'] = file_size / uncompressed_bytes
        
        return info
        
    except subprocess.CalledProcessError as e:
        logger.debug(f"Error analyzing FLAC file: {e}")
        if e.stderr:
            logger.debug(f"Error output: {e.stderr}")
        
        # If command-line tools fail, return basic file info
        return {
            'file_size': file_size,
            'error': str(e),
            'limited_analysis': True
        }
    except Exception as e:
        logger.debug(f"Unexpected error analyzing FLAC: {str(e)}")
        return None

def estimate_compression_level(info):
    """
    Estimate the FLAC compression level based on file analysis.
    Returns a tuple: (estimated_level, confidence)
    """
    # If we have limited analysis, use fallback method
    if info.get('limited_analysis', False):
        logger.info("Using limited analysis to estimate compression level")
        return estimate_level_from_file_size(info)
    
    # If we don't have enough info, we can't estimate
    required_keys = ['compression_ratio', 'min_blocksize', 'max_blocksize']
    if not all(key in info for key in required_keys):
        return (5, 0.1)  # Return default level with very low confidence
    
    # Calculate metrics
    ratio = info['compression_ratio']
    
    # These thresholds are approximations based on typical FLAC compression behavior
    # Ratio ranges for different levels (approximately)
    level_ranges = [
        (0.70, 1.00),  # Level 0 - least compression
        (0.67, 0.75),  # Level 1
        (0.65, 0.70),  # Level 2
        (0.62, 0.67),  # Level 3
        (0.60, 0.65),  # Level 4
        (0.58, 0.63),  # Level 5 - default
        (0.56, 0.60),  # Level 6
        (0.54, 0.58),  # Level 7
        (0.50, 0.56)   # Level 8 - most compression
    ]
    
    # Find which level range the ratio falls into
    matches = []
    for level, (min_ratio, max_ratio) in enumerate(level_ranges):
        if min_ratio <= ratio <= max_ratio:
            # Calculate how central it is in this range
            range_size = max_ratio - min_ratio
            if range_size > 0:
                centrality = 1 - abs((ratio - min_ratio) / range_size - 0.5) * 2
            else:
                centrality = 0
            matches.append((level, centrality))
    
    if not matches:
        # If no exact match, find the closest range
        closest_level = min(range(9), key=lambda l: min(abs(ratio - level_ranges[l][0]), abs(ratio - level_ranges[l][1])))
        confidence = 0.5  # Medium confidence for out-of-range estimate
        return (closest_level, confidence)
    
    # If multiple matches, use the one with highest centrality
    best_match = max(matches, key=lambda m: m[1])
    level, confidence = best_match
    
    # Adjust confidence based on blocksize variability
    if info['min_blocksize'] == info['max_blocksize']:
        # Fixed blocksize is common in level 0-2
        if level <= 2:
            confidence = min(confidence * 1.2, 1.0)
        else:
            confidence = confidence * 0.8
    else:
        # Variable blocksize is common in higher levels
        if level >= 3:
            confidence = min(confidence * 1.2, 1.0)
        else:
            confidence = confidence * 0.8
    
    return (level, confidence)

def estimate_level_from_file_size(info):
    """Fallback method to estimate compression level from file size only."""
    # This is a very rough estimation with low confidence
    return (5, 0.1)  # Always return default level with low confidence

def get_flac_compression_level(flac_file, threshold=0.7):
    """
    Analyze a FLAC file and return the estimated compression level.
    
    Args:
        flac_file: Path to the FLAC file
        threshold: Confidence threshold for returning a level (0.0-1.0)
        
    Returns:
        int: Estimated compression level (0-8), or 5 (default) if estimation fails
    """
    try:
        # Analyze the file
        info = analyze_flac_file(flac_file)
        if not info:
            logger.warning(f"Could not analyze FLAC file: {flac_file}")
            return 5  # Return default level
        
        # Estimate the compression level
        level, confidence = estimate_compression_level(info)
        
        logger.debug(f"Estimated compression level for {flac_file}: {level} (confidence: {confidence:.2f})")
        
        # If confidence is below threshold, use default level
        if confidence < threshold:
            logger.debug(f"Low confidence estimation ({confidence:.2f}), using default level")
            return 5
        
        return level
    except Exception as e:
        logger.error(f"Error determining compression level for {flac_file}: {str(e)}")
        return 5  # Return default level on error
