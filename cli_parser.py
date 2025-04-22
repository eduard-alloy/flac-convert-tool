#!/usr/bin/env python3
"""
Command-line interface parser for FLAC converter.
"""

import argparse
import multiprocessing

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Convert FLAC files to another audio format with metadata enhancement.')
    
    # Input source (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', help='Input directory containing FLAC files')
    input_group.add_argument('--db', help='Path to JSON database file')
    input_group.add_argument('--interactive', action='store_true', help='Run in interactive mode with the database')
    
    # Required arguments (except in interactive mode)
    parser.add_argument('--output', help='Output directory for converted files (required unless in interactive mode)')
    
    # Optional arguments for format and quality
    parser.add_argument('--format', default='mp3', choices=['mp3', 'aac', 'ogg', 'opus', 'm4a', 'flac'], 
                        help='Output format (default: mp3)')
    parser.add_argument('--bitrate', default='320k', help='Output bitrate (default: 320k)')
    parser.add_argument('--flac-compression', type=int, default=5, choices=range(0, 9),
                        help='FLAC compression level (0-8, default: 5, higher is more compressed)')
    
    # Optional filtering
    parser.add_argument('--artist', help='Filter by artist name (only with --db)')
    parser.add_argument('--artists', help='Filter by multiple artists, comma separated (only with --db)')
    parser.add_argument('--album-id', help='Filter by album ID (only with --db)')
    parser.add_argument('--year', help='Filter by release year (only with --db)')
    
    # Conversion options
    parser.add_argument('--threads', type=int, default=multiprocessing.cpu_count(),
                        help=f'Number of conversion threads (default: {multiprocessing.cpu_count()})')
    parser.add_argument('--skip-metadata', action='store_true', 
                        help='Skip metadata enhancement (useful if you encounter issues)')
    parser.add_argument('--lyrics', choices=['none', 'clean', 'timestamped'], default='clean',
                        help='How to handle lyrics: none (omit), clean (remove timestamps), timestamped (keep as is)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')
    parser.add_argument('--force', action='store_true',
                        help='Force reconversion of already converted files')
    
    # Base directory for database paths
    parser.add_argument('--base-dir', help='Base directory to prepend to paths in the database')
    
    # Tracking file
    parser.add_argument('--tracking-file', default='converted_files.json',
                        help='JSON file to track converted files (default: converted_files.json)')
    
    # Interactive mode options
    parser.add_argument('--db-path', help='Path to JSON database file for interactive mode')
    
    args = parser.parse_args()
    
    # Validate that output is provided when not in interactive mode
    if not args.interactive and not args.output:
        parser.error("--output is required when not in interactive mode")
    
    # If interactive is selected, ensure db_path is provided
    if args.interactive and not args.db_path:
        parser.error("--db-path is required with --interactive")
    
    return args
