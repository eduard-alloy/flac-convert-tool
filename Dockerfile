FROM python:3.10-slim

# Install FFmpeg, FLAC tools, and other dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg flac tk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy all Python modules and requirements
COPY *.py .
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create mount points for input, database, and output volumes
VOLUME ["/input", "/output", "/db"]

# Set environment variables for better interactive support
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TERM=xterm-256color
ENV DISPLAY=:0

# Set default command with unbuffered output
ENTRYPOINT ["python", "-u", "flac_converter.py"]
CMD ["--help"]
