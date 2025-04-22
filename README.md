# FLAC Audio Converter

A comprehensive Docker-based tool for converting FLAC audio files to various formats while preserving and enhancing metadata. This tool supports batch processing through a database, interactive artist selection, and intelligent FLAC compression analysis.

## Features

- **Multiple input modes**:
  - **Database mode**: Use a JSON database file to locate albums with filtering by artist, year, or album ID
  - **Directory mode**: Recursively convert files from an input directory
  - **Interactive mode**: Browse and select artists through a menu interface

- **Format support**:
  - **MP3**: Most compatible format with adjustable bitrate
  - **AAC**: Good for Apple devices
  - **OGG Vorbis**: Open-source format with good quality
  - **Opus**: Best compression ratio for lossy audio
  - **M4A**: Apple format (AAC in MP4 container)
  - **FLAC**: Lossless compression with adjustable levels

- **Advanced metadata handling**:
  - Album info from AlbumInfo.txt files
  - Track-specific details from .info files
  - Cover art embedding
  - Lyrics extraction and embedding (with timestamp options)

- **Intelligent handling**:
  - FLAC compression level detection
  - Conversion tracking to avoid redundant work
  - Multi-threaded processing for faster conversion
  - Fuzzy directory matching for database entries

- **Containerized for consistent operation**:
  - Works the same across operating systems
  - All dependencies included
  - No system-wide installations required

## Quick Start

1. **Clone or download this repository**

2. **Make the shell script executable**

   ```bash
   chmod +x build_and_run.sh
   ```

3. **Run in your preferred mode**

   Interactive mode (menu-based selection):
   ```bash
   ./build_and_run.sh --interactive /path/to/db.json [output_directory]
   ```
   
   Database mode (filter by artist):
   ```bash
   ./build_and_run.sh --db /path/to/db.json /path/to/output "Artist Name" mp3 320k
   ```
   
   Directory mode (convert all FLAC files in a directory):
   ```bash
   ./build_and_run.sh --input /path/to/flac/files /path/to/output mp3 320k
   ```

## Detailed Usage

### Database Mode

The database mode uses a JSON file to locate albums and FLAC files. The JSON should have this structure:

```json
{
  "album_id": {
    "path": "path/to/album/directory",
    "title": "Album Title",
    "artists": ["Artist Name"],
    "year": "Release Year"
  }
}
```

Run with:
```bash
./build_and_run.sh --db /path/to/db.json /path/to/output [artist] [format] [bitrate]
```

Optional arguments:
- `artist`: Filter by artist name
- `format`: Output format (mp3, aac, ogg, opus, m4a, flac)
- `bitrate`: Output bitrate (e.g., 320k, 256k)

Database filtering options:
- `--artist`: Filter by single artist
- `--artists`: Filter by multiple artists (comma-separated)
- `--album-id`: Filter by specific album ID
- `--year`: Filter by release year

### Interactive Mode

Interactive mode provides a text-based interface for selecting artists, format, and quality options:

```bash
./build_and_run.sh --interactive /path/to/db.json [output_directory]
```

The interface allows:
- Browsing artists by album count
- Searching for specific artists
- Selecting multiple artists at once
- Choosing output format and quality
- Seeing a summary before conversion

### Directory Mode

Directory mode converts all FLAC files in a directory and its subdirectories:

```bash
./build_and_run.sh --input /path/to/flac/files /path/to/output [format] [bitrate]
```

The directory structure will be preserved in the output folder.

### Format-Specific Options

#### MP3 options
```bash
./build_and_run.sh --db /path/to/db.json /path/to/output "Artist" mp3 --bitrate 320k
```

#### FLAC options
```bash
./build_and_run.sh --db /path/to/db.json /path/to/output "Artist" flac --flac-compression 8
```

FLAC compression levels (0-8):
| Level | Description                         | File Size | Encoding Speed |
|-------|-------------------------------------|-----------|----------------|
| 0     | Fastest, least compression          | Largest   | Very Fast      |
| 1     | Fast compression                    | Larger    | Fast           |
| 2     | Faster compression                  | Large     | Fast           |
| 3     | Balanced compression                | Medium    | Medium         |
| 4     | Better compression                  | Medium    | Medium         |
| 5     | Default compression (copy if same)  | Medium    | Medium         |
| 6     | Better compression, slower          | Smaller   | Slower         |
| 7     | High compression                    | Small     | Slow           |
| 8     | Highest compression                 | Smallest  | Very Slow      |

The FLAC format always provides lossless audio quality, regardless of compression level. The only differences are file size and encoding speed.

## Metadata Files

The script looks for and processes the following metadata files:

1. **Album Info Files**: Named `AlbumInfo.txt`, containing:
   - Album ID, title, artist, release date
   - Number of songs and duration
   - Track listing

   Example:
   ```
   [ID]          128791481
   [Title]       Modus Vivendi
   [Artists]     070 Shake
   [ReleaseDate] 2020-01-17
   [SongNum]     14
   [Duration]    2654

   [1]     Don't Break The Silence
   [2]     Come Around
   ```

2. **Track Info Files**: Named with the pattern `[track_number] - [artist] - [title].info`, containing:
   - Track title, album information, artist details
   - Copyright info, track/disc numbers
   - ISRC code, release date, audio quality
   - Composer information
   - Lyrics with timestamps

3. **Cover Art**: Image files (JPG, JPEG, PNG) in album directories
   - Automatically detects common naming patterns like "cover.jpg", "folder.jpg"
   - Falls back to any image in the directory if no standard name is found

## FLAC Analysis Tool

The package includes a tool to analyze FLAC files and estimate their compression level:

```bash
python flac_analyzer.py /path/to/file.flac
```

The tool provides:
- Basic file information
- Audio properties
- FLAC-specific details
- Compression analysis
- Estimated compression level

## Conversion Tracking

The script maintains a JSON file (by default named `converted_files.json`) that tracks which files have been converted. This helps:

- Skip already converted files to save time
- Track which version of each file has been converted
- Resume interrupted conversions
- Detect when source files have been modified

You can force reconversion of all files with the `--force` flag.

## Advanced Options

The Python script supports additional command-line arguments:

- `--threads`: Number of conversion threads (default: CPU count)
- `--skip-metadata`: Skip metadata enhancement
- `--lyrics`: How to handle lyrics: none, clean, timestamped
- `--verbose`: Enable detailed logging
- `--force`: Force reconversion of already converted files
- `--tracking-file`: JSON file to track converted files
- `--base-dir`: Base directory to prepend to paths in the database

## Project Structure

The project is organized into multiple modules for better maintainability:

- `flac_converter.py` - Main script and entry point
- `cli_parser.py` - Command-line argument parsing
- `db_handler.py` - Database handling and conversion tracking
- `file_finder.py` - Locating FLAC files from directory or database
- `metadata_parser.py` - Finding and parsing metadata files
- `file_converter.py` - Converting files and applying metadata
- `metadata_writer.py` - Applying metadata to different formats
- `interactive_mode.py` - Text-based interactive interface
- `flac_analyzer.py` - Standalone FLAC analysis tool
- `flac_level_detection.py` - FLAC compression level detection

## Troubleshooting

### Missing Albums

If albums are being skipped:

1. **Run with verbose logging**:
   ```bash
   ./build_and_run.sh --db /path/to/db.json /path/to/output "Artist" mp3 --verbose
   ```

2. **Check album paths** in the database vs. filesystem

3. **Try fuzzy matching** - The script will attempt to find matching directories based on album titles

### Conversion Errors

For errors during conversion:

1. **Check disk space** - Ensure sufficient space in output directory

2. **Skip metadata** if there are issues:
   ```bash
   ./build_and_run.sh --db /path/to/db.json /path/to/output "Artist" mp3 --skip-metadata
   ```

3. **Check permissions** - Ensure read/write access to input and output directories

## Requirements

All requirements are handled by the Docker container:

- Python 3.10
- FFmpeg
- Mutagen
- FLAC command-line tools (for compression level detection)

## Manual Docker Usage

If you prefer not to use the shell script:

1. **Build the Docker image**:
   ```bash
   docker build -t flac-converter .
   ```

2. **Run the container**:
   ```bash
   docker run --rm \
     -v /path/to/music:/input \
     -v /path/to/output:/output \
     flac-converter \
     --input /input \
     --output /output \
     --format mp3 \
     --bitrate 320k
   ```

## License

This project is open source under the MIT License.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## Acknowledgments

- FFmpeg for audio conversion
- Mutagen for metadata handling
- FLAC developers for the lossless audio format
