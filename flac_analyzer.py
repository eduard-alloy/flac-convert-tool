#!/usr/bin/env python3
"""
FLAC Analysis Tool - Extracts information from FLAC files and estimates compression level
"""

import os
import sys
import subprocess
import logging
import statistics
import math
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def analyze_flac_file(flac_file):
    """Analyze a FLAC file and extract technical information."""
    if not os.path.exists(flac_file):
        raise FileNotFoundError(f"File not found: {flac_file}")
        
    # Get file size
    file_size = os.path.getsize(flac_file)
    
    try:
        # Run flac command line tool with --show-blocksize flag
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
        logger.error(f"Error analyzing FLAC file: {e}")
        if e.stderr:
            logger.error(f"Error output: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return None

def estimate_compression_level(info):
    """
    Estimate the FLAC compression level based on file analysis.
    Returns a tuple: (estimated_level, confidence, metrics)
    """
    # If we don't have enough info, we can't estimate
    required_keys = ['compression_ratio', 'min_blocksize', 'max_blocksize']
    if not all(key in info for key in required_keys):
        return (None, 0, "Missing required information")
    
    # Metrics used for estimation
    metrics = {}
    
    # Calculate metrics
    metrics['compression_ratio'] = info['compression_ratio']
    metrics['ratio_score'] = 1 - info['compression_ratio']  # Higher ratio = better compression
    
    # Blocksize variability (higher level = more variable blocksize)
    if info['min_blocksize'] == info['max_blocksize']:
        metrics['blocksize_variability'] = 0
    else:
        metrics['blocksize_variability'] = info['max_blocksize'] / info['min_blocksize']
    
    # Framesize efficiency (higher level = more efficient frames)
    if info['max_framesize'] > 0:
        metrics['framesize_efficiency'] = 1 - (info['min_framesize'] / info['max_framesize'])
    else:
        metrics['framesize_efficiency'] = 0
    
    # Combine metrics to estimate level
    # Typical compression ratio ranges from ~0.65 for level 0 to ~0.55 for level 8
    # We'll use this as the primary indicator
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
        return (closest_level, confidence, metrics)
    
    # If multiple matches, use the one with highest centrality
    best_match = max(matches, key=lambda m: m[1])
    level, confidence = best_match
    
    # Include framesize and blocksize in confidence calculation
    confidence = 0.7 * confidence + 0.2 * metrics['framesize_efficiency'] + 0.1 * min(1, metrics['blocksize_variability'])
    
    return (level, confidence, metrics)

def format_size(size_bytes):
    """Format byte size to human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024):.2f} MB"
    else:
        return f"{size_bytes/(1024*1024*1024):.2f} GB"

def print_flac_analysis(flac_file):
    """Analyze a FLAC file and print the results."""
    print(f"\nAnalyzing FLAC file: {os.path.basename(flac_file)}")
    print("-" * 60)
    
    try:
        info = analyze_flac_file(flac_file)
        if not info:
            print("Analysis failed.")
            return
        
        # Print basic file information
        file_size = info.get('file_size', 0)
        print(f"File size: {format_size(file_size)}")
        
        # Print audio properties
        print("\nAudio Properties:")
        if 'channels' in info:
            print(f"  Channels: {info['channels']}")
        if 'sample_rate' in info:
            print(f"  Sample Rate: {info['sample_rate']} Hz")
        if 'bits_per_sample' in info:
            print(f"  Bit Depth: {info['bits_per_sample']} bits")
        if 'duration' in info:
            print(f"  Duration: {info['duration']}")
        
        # Print FLAC-specific information
        print("\nFLAC Properties:")
        if 'min_blocksize' in info and 'max_blocksize' in info:
            print(f"  Block Size: {info['min_blocksize']} to {info['max_blocksize']}")
        if 'min_framesize' in info and 'max_framesize' in info:
            print(f"  Frame Size: {info['min_framesize']} to {info['max_framesize']} bytes")
        
        # Print compression information
        print("\nCompression Analysis:")
        if 'uncompressed_size' in info:
            uncompressed_size = info['uncompressed_size']
            print(f"  Uncompressed Size: {format_size(uncompressed_size)}")
            if 'compression_ratio' in info:
                ratio = info['compression_ratio']
                print(f"  Compression Ratio: {ratio:.4f} ({ratio*100:.1f}% of original)")
        
        # Estimate compression level
        level, confidence, metrics = estimate_compression_level(info)
        print("\nCompression Level Estimation:")
        if level is not None:
            confidence_desc = "Very Low" if confidence < 0.3 else "Low" if confidence < 0.5 else "Medium" if confidence < 0.7 else "High" if confidence < 0.9 else "Very High"
            print(f"  Estimated Level: {level} (Confidence: {confidence_desc}, {confidence:.2f})")
            print(f"  Note: FLAC compression level is an estimation as it's not stored in the file")
            
            # Print metrics used for estimation
            print("\nMetrics Used for Estimation:")
            for key, value in metrics.items():
                print(f"  {key}: {value:.4f}")
        else:
            print("  Could not estimate compression level")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <flac_file>")
        sys.exit(1)
    
    flac_file = sys.argv[1]
    print_flac_analysis(flac_file)
