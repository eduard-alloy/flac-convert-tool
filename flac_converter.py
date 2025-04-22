#!/usr/bin/env python3
"""
FLAC to Audio Converter with Metadata Enhancement and Library Database Support

This script converts FLAC files to other formats while preserving and enhancing metadata
from separate info files. It can use a JSON database file to locate albums and can filter
by artist. It also tracks converted files to avoid redundant conversions.

Usage:
    python flac_converter.py --db /path/to/db.json --output /path/to/output/mp3s --artist "070 Shake" --format mp3
    python flac_converter.py --input /path/to/flac/files --output /path/to/output/mp3s --format mp3 --bitrate 320k
    python flac_converter.py --interactive --db-path /path/to/db.json
"""

import os
import logging
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# Import modules
from file_finder import find_flac_files, find_flac_files_from_db
from metadata_parser import find_album_info, find_track_info_files, find_cover_art
from file_converter import convert_file, create_output_dir_structure, should_convert
from db_handler import read_database, load_conversion_tracking
from cli_parser import parse_arguments

# Set up logging
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the script."""
    args = parse_arguments()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handle interactive mode if selected
    if args.interactive:
        try:
            from interactive_mode import run_interactive_mode
            import tempfile
            
            # Get interactive selections
            interactive_options = run_interactive_mode(args.db_path)
            if not interactive_options:
                logger.info("Interactive session cancelled or no options selected.")
                return
            
            # Set up arguments based on interactive selection
            args.db = args.db_path
            
            # Ask for output directory if not provided
            if not args.output:
                try:
                    import tkinter as tk
                    from tkinter import filedialog
                    
                    root = tk.Tk()
                    root.withdraw()  # Hide the main window
                    
                    print("\nPlease select an output directory for the converted files:")
                    output_dir = filedialog.askdirectory(title="Select Output Directory")
                    
                    if not output_dir:
                        logger.info("No output directory selected. Exiting.")
                        return
                        
                    args.output = output_dir
                except Exception as e:
                    logger.error(f"Error opening file dialog: {str(e)}")
                    print("\nPlease enter an output directory path:")
                    args.output = input().strip()
                    if not args.output:
                        logger.info("No output directory provided. Exiting.")
                        return
            
            # Set format and bitrate from interactive selection
            args.format = interactive_options['format']
            args.bitrate = interactive_options['bitrate']
            
            # Handle FLAC compression level if applicable
            if args.format == 'flac' and 'flac_compression' in interactive_options:
                args.flac_compression = interactive_options['flac_compression']
            
            # Handle multiple artists
            if len(interactive_options['artists']) == 1:
                args.artist = interactive_options['artists'][0]
            else:
                # Use a comma-separated list for db filtering
                args.artists = ",".join(interactive_options['artists'])
                
                # Also write to a temporary file for future reference
                try:
                    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as f:
                        for artist in interactive_options['artists']:
                            f.write(f"{artist}\n")
                        args.artists_file = f.name
                except Exception as e:
                    logger.warning(f"Could not create temporary file for artists: {str(e)}")
        
        except ImportError:
            logger.error("Interactive mode module not available")
            return
        except Exception as e:
            logger.error(f"Error in interactive mode: {str(e)}")
            return
    
    # Initialize tracking file
    tracking_path = args.tracking_file
    if not os.path.isabs(tracking_path):
        tracking_path = os.path.join(args.output, tracking_path)
    
    # Validate output directory
    output_dir = os.path.abspath(args.output)
    os.makedirs(output_dir, exist_ok=True)
    
    # Find FLAC files - either from directory or database
    if args.db:
        # Use database approach
        logger.info(f"Using database file: {args.db}")
        
        # If base_dir isn't explicitly set, use the directory containing the database file
        if args.base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(args.db))
            logger.info(f"Using database directory as base directory: {base_dir}")
        else:
            base_dir = args.base_dir
        
        # Handle multiple artists if provided
        artist_filter = None
        if hasattr(args, 'artists') and args.artists:
            artist_list = [a.strip() for a in args.artists.split(',')]
            logger.info(f"Filtering by {len(artist_list)} artists")
            
            # Read the database and filter by each artist
            all_albums = {}
            for artist in artist_list:
                artist_albums = read_database(
                    args.db,
                    base_dir=base_dir,
                    artist_filter=artist,
                    album_id_filter=args.album_id,
                    year_filter=args.year
                )
                all_albums.update(artist_albums)
            
            albums = all_albums
        else:
            # Standard single artist filter
            albums = read_database(
                args.db,
                base_dir=base_dir,
                artist_filter=args.artist,
                album_id_filter=args.album_id,
                year_filter=args.year
            )
        
        if not albums:
            logger.error("No albums found in database matching the criteria")
            return
            
        # Find FLAC files from database entries
        flac_files = find_flac_files_from_db(albums, base_dir)
        
        # For directory-based operations, set the base input dir
        input_dir = base_dir
    else:
        # Use directory approach
        input_dir = os.path.abspath(args.input)
        if not os.path.isdir(input_dir):
            logger.error(f"Input directory does not exist: {input_dir}")
            return
            
        logger.info(f"Searching for FLAC files in {input_dir}...")
        flac_files = find_flac_files(input_dir)
    
    if not flac_files:
        logger.warning(f"No FLAC files found")
        return
    
    logger.info(f"Found {len(flac_files)} FLAC files to convert to {args.format}")
    
    # Find metadata files
    logger.info("Searching for metadata files...")
    
    # For database mode, only search in directories where FLAC files were found
    if args.db:
        search_dirs = set(os.path.dirname(flac_file[0]) for flac_file in flac_files)
        
        album_info = {}
        for directory in search_dirs:
            album_info.update(find_album_info(directory))
            
        track_info_files = {}
        for directory in search_dirs:
            track_info_files.update(find_track_info_files(directory))
            
        cover_files = {}
        for directory in search_dirs:
            cover_files.update(find_cover_art(directory))
    else:
        # Standard directory mode
        album_info = find_album_info(input_dir)
        track_info_files = find_track_info_files(input_dir)
        cover_files = find_cover_art(input_dir)
    
    logger.info(f"Found {len(album_info)} album info files")
    logger.info(f"Found {len(track_info_files)} track info files")
    logger.info(f"Found {len(cover_files)} cover art files")
    
    # Report on tracking data
    tracking_data = load_conversion_tracking(tracking_path)
    already_converted = sum(1 for flac_file in [f[0] for f in flac_files] if flac_file in tracking_data)
    logger.info(f"Found {already_converted} previously converted files")
    
    # Filter out files that don't need conversion if not forcing
    if not args.force:
        files_to_convert = []
        skipped_files = 0
        
        for flac_file_info in flac_files:
            flac_file = flac_file_info[0]
            output_path = create_output_dir_structure(input_dir, output_dir, flac_file)
            output_filename = os.path.splitext(os.path.basename(flac_file))[0] + f'.{args.format}'
            output_file = os.path.join(output_path, output_filename)
            
            if should_convert(flac_file, output_file, tracking_path, args.force):
                files_to_convert.append(flac_file_info)
            else:
                skipped_files += 1
        
        if skipped_files > 0:
            logger.info(f"Skipping {skipped_files} already converted files (use --force to reconvert)")
            flac_files = files_to_convert
    
    # Prepare conversion arguments
    if args.format == 'flac':
        # For FLAC output, include compression level
        compression_level = getattr(args, 'flac_compression', 5)  # Default to level 5 if not specified
        logger.info(f"Using FLAC compression level: {compression_level}")
        
        conversion_args = [
            (flac_file_info, input_dir, output_dir, args.format, args.bitrate, album_info, 
             track_info_files, cover_files, tracking_path, args.force, args.skip_metadata, args.lyrics, compression_level) 
            for flac_file_info in flac_files
        ]
    else:
        # Standard arguments for other formats
        conversion_args = [
            (flac_file_info, input_dir, output_dir, args.format, args.bitrate, album_info, 
             track_info_files, cover_files, tracking_path, args.force, args.skip_metadata, args.lyrics) 
            for flac_file_info in flac_files
        ]
    
    # Convert files using a thread pool
    successful = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        with tqdm(total=len(flac_files), desc="Converting", unit="file") as pbar:
            for success, file in executor.map(convert_file, conversion_args):
                if success:
                    successful += 1
                else:
                    failed += 1
                pbar.update(1)
    
    # Report results
    logger.info(f"Conversion complete: {successful} successful, {failed} failed")
    if successful > 0:
        logger.info(f"Converted files are in {output_dir}")
    
    # Print tracking summary
    final_tracking = load_conversion_tracking(tracking_path)
    logger.info(f"Total tracked conversions: {len(final_tracking)}")
    
    # Clean up any temporary files
    if args.interactive and hasattr(args, 'artists_file') and os.path.exists(args.artists_file):
        try:
            os.unlink(args.artists_file)
        except Exception as e:
            logger.warning(f"Could not remove temporary file: {str(e)}")

if __name__ == "__main__":
    main()
