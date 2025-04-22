#!/bin/bash
# build_and_run.sh - Script to build and run the FLAC converter Docker container

# Stop on errors
set -e

# Define variables
IMAGE_NAME="flac-converter"
TAG="latest"

# Display usage info if no arguments
if [ $# -lt 1 ]; then
  echo "Usage:"
  echo "  Interactive mode: $0 --interactive <db_file> [output_directory]"
  echo "  Database mode: $0 --db <db_file> <output_directory> [artist] [format] [bitrate]"
  echo "  Directory mode: $0 --input <input_directory> <output_directory> [format] [bitrate]"
  echo ""
  echo "Examples:"
  echo "  $0 --interactive ~/Music/db.json"
  echo "  $0 --db ~/Music/db.json ~/Music/mp3 \"070 Shake\" mp3 320k"
  echo "  $0 --input ~/Music/flac ~/Music/mp3 mp3 320k"
  echo ""
  echo "Debug options:"
  echo "  --verbose: Enable verbose logging"
  echo "  --force: Force reconversion of already converted files"
  exit 1
fi

# Parse mode
MODE=$1
shift

# Set defaults
VERBOSE=""
FORCE=""

# Parse any debug flags and remove them from the arguments
ARGS=()
for arg in "$@"; do
  if [ "$arg" = "--verbose" ]; then
    VERBOSE="--verbose"
  elif [ "$arg" = "--force" ]; then
    FORCE="--force"
  else
    ARGS+=("$arg")
  fi
done

# Restore arguments without the flags
set -- "${ARGS[@]}"

# Build the Docker image
echo "Building Docker image: $IMAGE_NAME:$TAG"
docker build -t "$IMAGE_NAME:$TAG" .

if [ "$MODE" = "--interactive" ]; then
  # Interactive mode
  if [ $# -lt 1 ]; then
    echo "Error: Interactive mode requires a database file"
    exit 1
  fi
  
  DB_FILE=$(realpath "$1")
  OUTPUT_DIR=""
  
  if [ $# -ge 2 ]; then
    OUTPUT_DIR=$(realpath "$2")
  fi
  
  # Check if database file exists
  if [ ! -f "$DB_FILE" ]; then
    echo "Error: Database file does not exist: $DB_FILE"
    exit 1
  fi
  
  # Run the container in interactive mode
  echo "Running FLAC converter in interactive mode with database $DB_FILE"
  
  OUTPUT_ARGS=""
  if [ -n "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR"
    OUTPUT_ARGS="--output /output"
    VOLUME_ARGS="-v \"$OUTPUT_DIR:/output\""
  else
    # When no output directory is specified, we'll mount the current directory
    # The script will ask for output location via the GUI
    OUTPUT_DIR=$(pwd)
    VOLUME_ARGS="-v \"$OUTPUT_DIR:/output\""
  fi
  
  # Need to run with interactive TTY and proper terminal settings
  docker run --rm -it \
    -v "$(dirname "$DB_FILE"):/db" \
    -v "$OUTPUT_DIR:/output" \
    -e PYTHONUNBUFFERED=1 \
    -e TERM=$TERM \
    "$IMAGE_NAME:$TAG" \
    --interactive \
    --db-path "/db/$(basename "$DB_FILE")" \
    $OUTPUT_ARGS \
    $VERBOSE \
    $FORCE

elif [ "$MODE" = "--db" ]; then
  # Database mode
  if [ $# -lt 2 ]; then
    echo "Error: Database mode requires at least a database file and output directory"
    exit 1
  fi
  
  DB_FILE=$(realpath "$1")
  OUTPUT_DIR=$(realpath "$2")
  ARTIST=${3:-""}
  FORMAT=${4:-mp3}
  BITRATE=${5:-320k}
  
  # Check if database file exists
  if [ ! -f "$DB_FILE" ]; then
    echo "Error: Database file does not exist: $DB_FILE"
    exit 1
  fi
  
  # Create output directory if it doesn't exist
  mkdir -p "$OUTPUT_DIR"
  
  # Run the container
  echo "Running FLAC conversion using database $DB_FILE, artist filter: $ARTIST"
  
  ARTIST_ARGS=""
  if [ -n "$ARTIST" ]; then
    ARTIST_ARGS="--artist \"$ARTIST\""
  fi
  
  # Handle format and additional options
  FORMAT_ARGS=""
  if [ -n "$FORMAT" ]; then
    FORMAT_ARGS="--format $FORMAT"
    
    # Add bitrate for non-FLAC formats
    if [ "$FORMAT" != "flac" ] && [ -n "$BITRATE" ]; then
      FORMAT_ARGS="$FORMAT_ARGS --bitrate $BITRATE"
    fi
    
    # Add compression level if FLAC format is selected and a 6th argument is provided
    if [ "$FORMAT" = "flac" ] && [ $# -ge 6 ]; then
      FORMAT_ARGS="$FORMAT_ARGS --flac-compression $6"
    fi
  fi
  
  # Handle different debug flags
  EXTRA_OPTIONS="$VERBOSE $FORCE"
  
  docker run --rm \
    -v "$(dirname "$DB_FILE"):/db" \
    -v "$OUTPUT_DIR:/output" \
    "$IMAGE_NAME:$TAG" \
    --db "/db/$(basename "$DB_FILE")" \
    --output /output \
    $FORMAT_ARGS \
    $ARTIST_ARGS \
    $EXTRA_OPTIONS
  
elif [ "$MODE" = "--input" ]; then
  # Directory mode
  if [ $# -lt 2 ]; then
    echo "Error: Directory mode requires at least an input and output directory"
    exit 1
  fi
  
  INPUT_DIR=$(realpath "$1")
  OUTPUT_DIR=$(realpath "$2")
  FORMAT=${3:-mp3}
  BITRATE=${4:-320k}
  
  # Check if input directory exists
  if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory does not exist: $INPUT_DIR"
    exit 1
  fi
  
  # Create output directory if it doesn't exist
  mkdir -p "$OUTPUT_DIR"
  
  # Handle format and additional options
  FORMAT_ARGS=""
  if [ -n "$FORMAT" ]; then
    FORMAT_ARGS="--format $FORMAT"
    
    # Add bitrate for non-FLAC formats
    if [ "$FORMAT" != "flac" ] && [ -n "$BITRATE" ]; then
      FORMAT_ARGS="$FORMAT_ARGS --bitrate $BITRATE"
    fi
    
    # Add compression level if FLAC format is selected and a 5th argument is provided
    if [ "$FORMAT" = "flac" ] && [ $# -ge 5 ]; then
      FORMAT_ARGS="$FORMAT_ARGS --flac-compression $5"
    fi
  fi
  
  # Handle different debug flags
  EXTRA_OPTIONS="$VERBOSE $FORCE"
  
  # Run the container
  echo "Running FLAC conversion from $INPUT_DIR to $OUTPUT_DIR"
  docker run --rm \
    -v "$INPUT_DIR:/input" \
    -v "$OUTPUT_DIR:/output" \
    "$IMAGE_NAME:$TAG" \
    --input /input \
    --output /output \
    $FORMAT_ARGS \
    $EXTRA_OPTIONS
else
  echo "Error: Unknown mode $MODE. Use --interactive, --db, or --input."
  exit 1
fi

echo "Conversion complete!"
