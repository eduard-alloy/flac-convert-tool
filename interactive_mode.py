#!/usr/bin/env python3
"""
Interactive dialog interface for FLAC converter.
Provides a text-based menu to select artists, format, and bitrate.
"""

import os
import json
import sys
from collections import Counter, defaultdict

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    """Print a formatted header."""
    term_width = os.get_terminal_size().columns
    print("\n" + "=" * term_width)
    print(title.center(term_width))
    print("=" * term_width + "\n")

def read_database(db_file):
    """Read the JSON database file."""
    try:
        with open(db_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading database: {str(e)}")
        sys.exit(1)

def get_all_artists(database):
    """Extract all artists from the database with album counts."""
    artists = Counter()
    
    for album_id, album_data in database.items():
        for artist in album_data.get('artists', []):
            artists[artist] += 1
    
    return artists

def get_artist_albums(database, selected_artist):
    """Get all albums by the selected artist."""
    albums = []
    
    for album_id, album_data in database.items():
        if selected_artist in album_data.get('artists', []):
            albums.append((album_id, album_data))
    
    return sorted(albums, key=lambda x: x[1].get('year', '0000'))

def format_artist_menu(artists):
    """Format the artist selection menu."""
    sorted_artists = sorted(artists.items(), key=lambda x: (-x[1], x[0]))
    menu = []
    
    for i, (artist, count) in enumerate(sorted_artists, 1):
        menu.append(f"{i:3}. {artist} ({count} album{'s' if count > 1 else ''})")
    
    return menu, sorted_artists

def select_artists(database):
    """Interactive menu to select artists."""
    all_artists = get_all_artists(database)
    
    while True:
        clear_screen()
        print_header("Select Artists")
        
        if not all_artists:
            print("No artists found in the database.")
            return []
        
        menu_items, sorted_artists = format_artist_menu(all_artists)
        
        # Display top 20 artists and option to search
        print("Top artists by album count:")
        for item in menu_items[:20]:
            print(item)
            
        if len(menu_items) > 20:
            print(f"\n... and {len(menu_items) - 20} more artists.")
            print("\nType 'more' to see all artists")
            print("Type 'search' to search for an artist")
        
        print("\nEnter artist numbers separated by commas, 'all' for all artists,")
        print("'done' when finished selecting, or 'quit' to exit.")
        
        current_selected = []
        selection = input("\nSelection: ").strip().lower()
        
        if selection == 'quit':
            sys.exit(0)
        elif selection == 'all':
            return [artist for artist, _ in sorted_artists]
        elif selection == 'more':
            while True:
                clear_screen()
                print_header("All Artists")
                
                # Display all artists in pages
                page_size = 30
                total_pages = (len(menu_items) + page_size - 1) // page_size
                
                page = 1
                while page <= total_pages:
                    clear_screen()
                    print_header(f"All Artists (Page {page}/{total_pages})")
                    
                    start_idx = (page - 1) * page_size
                    end_idx = min(start_idx + page_size, len(menu_items))
                    
                    for item in menu_items[start_idx:end_idx]:
                        print(item)
                    
                    nav = input("\nEnter artist numbers, 'n' for next page, 'p' for previous, 'b' to go back: ").strip().lower()
                    
                    if nav == 'n' and page < total_pages:
                        page += 1
                    elif nav == 'p' and page > 1:
                        page -= 1
                    elif nav == 'b':
                        break
                    else:
                        try:
                            # Try to parse as artist selection
                            nums = [int(n.strip()) for n in nav.split(',') if n.strip()]
                            current_selected = [sorted_artists[i-1][0] for i in nums if 1 <= i <= len(sorted_artists)]
                            return current_selected
                        except ValueError:
                            pass
                            
                break  # Go back to main menu
                
        elif selection == 'search':
            search_term = input("\nEnter search term: ").strip().lower()
            search_results = [(i, artist, count) for i, (artist, count) in enumerate(sorted_artists, 1) 
                             if search_term in artist.lower()]
            
            if search_results:
                clear_screen()
                print_header("Search Results")
                
                for i, artist, count in search_results:
                    print(f"{i:3}. {artist} ({count} album{'s' if count > 1 else ''})")
                
                search_selection = input("\nEnter artist numbers or 'b' to go back: ").strip().lower()
                
                if search_selection == 'b':
                    continue
                
                try:
                    nums = [int(n.strip()) for n in search_selection.split(',') if n.strip()]
                    current_selected = [sorted_artists[i-1][0] for i in nums if 1 <= i <= len(sorted_artists)]
                    return current_selected
                except ValueError:
                    print("Invalid selection. Please try again.")
            else:
                input(f"No artists found matching '{search_term}'. Press Enter to continue...")
        
        elif selection == 'done':
            return current_selected
        
        else:
            try:
                nums = [int(n.strip()) for n in selection.split(',') if n.strip()]
                current_selected = [sorted_artists[i-1][0] for i in nums if 1 <= i <= len(sorted_artists)]
                return current_selected
            except ValueError:
                print("Invalid selection. Please try again.")
                input("Press Enter to continue...")

def select_format_and_bitrate():
    """Interactive menu to select output format and bitrate."""
    formats = {
        '1': ('mp3', ['128k', '192k', '256k', '320k']),
        '2': ('aac', ['128k', '192k', '256k', '320k']),
        '3': ('ogg', ['128k', '192k', '256k', '320k']),
        '4': ('opus', ['96k', '128k', '192k', '256k']),
        '5': ('m4a', ['128k', '192k', '256k', '320k']),
        '6': ('flac', ['compression']),
    }
    
    default_bitrates = {
        'mp3': '320k',
        'aac': '256k',
        'ogg': '256k',
        'opus': '128k',
        'm4a': '256k',
    }
    
    flac_compression_levels = {
        '1': '0 (fastest, least compression)',
        '2': '1',
        '3': '2',
        '4': '3',
        '5': '4',
        '6': '5 (default)',
        '7': '6',
        '8': '7',
        '9': '8 (slowest, most compression)',
    }
    
    while True:
        clear_screen()
        print_header("Select Format and Bitrate")
        
        print("Available formats:")
        print("1. MP3 (Most compatible)")
        print("2. AAC (Good for Apple devices)")
        print("3. OGG Vorbis (Open format, good quality)")
        print("4. Opus (Best compression, modern)")
        print("5. M4A (Apple format, AAC in MP4 container)")
        print("6. FLAC (Lossless compression)")
        
        format_choice = input("\nSelect format [1-6] (default: 1): ").strip()
        if not format_choice:
            format_choice = '1'
        
        if format_choice not in formats:
            print("Invalid selection. Please try again.")
            input("Press Enter to continue...")
            continue
        
        selected_format, bitrate_options = formats[format_choice]
        
        # Special handling for FLAC (compression level instead of bitrate)
        if selected_format == 'flac':
            print(f"\nSelected format: {selected_format.upper()}")
            print(f"\nCompression levels for FLAC:")
            
            for num, desc in flac_compression_levels.items():
                print(f"{num}. Level {desc}")
            
            compression_choice = input(f"\nSelect compression level [1-9] (default: 6): ").strip()
            
            if not compression_choice:
                compression_level = 5  # Default is level 5
            else:
                try:
                    level_num = int(compression_choice)
                    if 1 <= level_num <= 9:
                        compression_level = level_num - 1  # Convert from 1-9 to 0-8
                    else:
                        raise ValueError
                except ValueError:
                    print("Invalid selection. Using default compression level (5).")
                    compression_level = 5
                    input("Press Enter to continue...")
            
            print(f"\nSelected: {selected_format.upper()} with compression level {compression_level}")
            confirm = input("\nConfirm selection? (Y/n): ").strip().lower()
            
            if confirm != 'n':
                # For FLAC, the compression level is returned instead of bitrate
                return selected_format, str(compression_level)
        else:
            # Standard bitrate selection for other formats
            default_bitrate = default_bitrates[selected_format]
            
            print(f"\nSelected format: {selected_format.upper()}")
            print(f"\nAvailable bitrates for {selected_format.upper()}:")
            
            for i, bitrate in enumerate(bitrate_options, 1):
                is_default = " (default)" if bitrate == default_bitrate else ""
                print(f"{i}. {bitrate}{is_default}")
            
            bitrate_choice = input(f"\nSelect bitrate [1-{len(bitrate_options)}] (default: {bitrate_options.index(default_bitrate)+1}): ").strip()
            
            if not bitrate_choice:
                selected_bitrate = default_bitrate
            else:
                try:
                    idx = int(bitrate_choice) - 1
                    if 0 <= idx < len(bitrate_options):
                        selected_bitrate = bitrate_options[idx]
                    else:
                        raise ValueError
                except ValueError:
                    print("Invalid selection. Using default bitrate.")
                    selected_bitrate = default_bitrate
                    input("Press Enter to continue...")
            
            print(f"\nSelected: {selected_format.upper()} at {selected_bitrate}")
            confirm = input("\nConfirm selection? (Y/n): ").strip().lower()
            
            if confirm != 'n':
                return selected_format, selected_bitrate

def confirm_conversion(selected_artists, format_name, bitrate, database):
    """Show a summary and confirm the conversion."""
    clear_screen()
    print_header("Conversion Summary")
    
    # Count albums and tracks
    album_count = 0
    albums_by_artist = defaultdict(list)
    
    for album_id, album_data in database.items():
        for artist in album_data.get('artists', []):
            if artist in selected_artists:
                album_count += 1
                albums_by_artist[artist].append(album_data.get('title', 'Unknown Album'))
                break
    
    print(f"You've selected {len(selected_artists)} artist(s):")
    for artist in selected_artists:
        print(f"- {artist} ({len(albums_by_artist[artist])} albums)")
    
    # Format display based on format type
    if format_name == 'flac':
        print(f"\nFormat: {format_name.upper()} with compression level {bitrate}")
    else:
        print(f"\nFormat: {format_name.upper()} at {bitrate}")
    
    print(f"Total albums to convert: {album_count}")
    
    print("\nThis will scan for FLAC files in these albums and convert them.")
    confirm = input("\nProceed with conversion? (Y/n): ").strip().lower()
    
    return confirm != 'n'

def run_interactive_mode(db_file):
    """Run the interactive selection mode."""
    database = read_database(db_file)
    
    # Select artists
    selected_artists = select_artists(database)
    if not selected_artists:
        print("No artists selected. Exiting.")
        return None
    
    # Select format and bitrate
    format_name, bitrate = select_format_and_bitrate()
    
    # Confirm conversion
    if not confirm_conversion(selected_artists, format_name, bitrate, database):
        print("Conversion cancelled. Exiting.")
        return None
    
    # For FLAC format, store compression level
    extra_options = {}
    if format_name == 'flac':
        extra_options['flac_compression'] = int(bitrate)
    
    # Return the selected options
    result = {
        'artists': selected_artists,
        'format': format_name,
        'bitrate': bitrate if format_name != 'flac' else '320k',  # Default bitrate for non-FLAC formats
    }
    
    # Add extra options
    result.update(extra_options)
    
    return result

if __name__ == "__main__":
    # Test the interactive mode
    if len(sys.argv) > 1:
        options = run_interactive_mode(sys.argv[1])
        print(f"Selected options: {options}")
    else:
        print("Please provide a database file path.")
