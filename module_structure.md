# FLAC Converter: Updated Module Structure

## Core Modules

1. **flac_converter.py**
   - Main entry point and orchestration
   - Handles command-line arguments and interactive mode

2. **cli_parser.py**
   - Parse command-line arguments
   - Define available options and defaults

3. **db_handler.py**
   - Read JSON database
   - Track conversion history
   - Filter albums by criteria

4. **file_finder.py**
   - Locate FLAC files in directories
   - Find files based on database entries

5. **metadata_parser.py**
   - Parse album info files
   - Extract information from track info files
   - Locate cover art files

6. **file_converter.py**
   - Handle actual file conversion
   - Create directory structure
   - Track converted files

7. **metadata_writer.py** (New)
   - Apply metadata to different formats
   - Support MP3, AAC, M4A, OGG, OPUS
   - Handle cover art embedding

8. **interactive_mode.py**
   - Text-based interactive interface
   - Artist selection and filtering
   - Format and bitrate selection

## Support Files

- **__init__.py**
   - Package definition
   - Version information

- **requirements.txt**
   - Required Python packages

- **Dockerfile**
   - Docker container configuration

- **build_and_run.sh**
   - Script to build and run the Docker container

## Module Relationships

```
                 ┌────────────────┐
                 │flac_converter.py│
                 └────────┬───────┘
           ┌──────────────┼──────────────┐
           │              │              │
┌──────────▼─────┐ ┌──────▼───────┐ ┌────▼────────────┐
│  cli_parser.py │ │ db_handler.py│ │interactive_mode.py│
└────────────────┘ └──────────────┘ └─────────────────┘
           │              │              │
           │              │              │
┌──────────▼─────┐ ┌──────▼───────┐ ┌────▼────────────┐
│ file_finder.py │ │file_converter.py│ │ metadata_parser.py│
└────────────────┘ └──────┬───────┘ └─────────────────┘
                          │
                 ┌────────▼───────┐
                 │metadata_writer.py│
                 └────────────────┘
```
