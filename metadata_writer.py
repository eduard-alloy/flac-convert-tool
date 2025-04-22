#!/usr/bin/env python3
"""
Metadata writing functions for FLAC converter.
Handles applying metadata to converted audio files in various formats.
"""

import os
import re
import logging
import base64

# Set up logging
logger = logging.getLogger(__name__)

def apply_mp3_metadata(mp3_file, track_metadata, album_metadata, cover_art):
    """Apply metadata to an MP3 file using mutagen."""
    try:
        from mutagen.id3 import ID3, APIC, USLT, TIT2, TALB, TPE1, TPE2, TRCK, TPOS, TYER, TCOM, TXXX, TSRC
        
        # Create ID3 tags if they don't exist
        try:
            tags = ID3(mp3_file)
        except:
            # If the file doesn't have an ID3 tag, create one
            tags = ID3()
        
        # Apply track metadata
        if 'title' in track_metadata:
            tags['TIT2'] = TIT2(encoding=3, text=track_metadata['title'])
        
        if 'artist' in track_metadata:
            tags['TPE1'] = TPE1(encoding=3, text=track_metadata['artist'])
        
        if 'album_artist' in track_metadata:
            tags['TPE2'] = TPE2(encoding=3, text=track_metadata['album_artist'])
        
        if 'album' in track_metadata:
            tags['TALB'] = TALB(encoding=3, text=track_metadata['album'])
        
        # Track number and total
        if 'track_number' in track_metadata and 'total_tracks' in track_metadata:
            tags['TRCK'] = TRCK(encoding=3, text=f"{track_metadata['track_number']}/{track_metadata['total_tracks']}")
        elif 'track_number' in track_metadata:
            tags['TRCK'] = TRCK(encoding=3, text=track_metadata['track_number'])
        
        # Disc number and total
        if 'disc_number' in track_metadata and 'total_discs' in track_metadata:
            tags['TPOS'] = TPOS(encoding=3, text=f"{track_metadata['disc_number']}/{track_metadata['total_discs']}")
        elif 'disc_number' in track_metadata:
            tags['TPOS'] = TPOS(encoding=3, text=track_metadata['disc_number'])
        
        # Release date
        if 'release_date' in track_metadata:
            year_match = re.search(r'(\d{4})', track_metadata['release_date'])
            if year_match:
                tags['TYER'] = TYER(encoding=3, text=year_match.group(1))
        
        # ISRC
        if 'isrc' in track_metadata:
            tags['TSRC'] = TSRC(encoding=3, text=track_metadata['isrc'])
        
        # Composer
        if 'composer' in track_metadata:
            tags['TCOM'] = TCOM(encoding=3, text=track_metadata['composer'])
        
        # Copyright
        if 'copyright' in track_metadata:
            tags['TXXX:COPYRIGHT'] = TXXX(encoding=3, desc='COPYRIGHT', text=track_metadata['copyright'])
        
        # Lyrics
        if 'lyrics' in track_metadata:
            tags['USLT'] = USLT(encoding=3, lang='eng', desc='', text=track_metadata['lyrics'])
        
        # Cover art
        if cover_art and os.path.exists(cover_art):
            with open(cover_art, 'rb') as img:
                image_data = img.read()
                mime = 'image/jpeg' if cover_art.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
                tags['APIC'] = APIC(
                    encoding=3,
                    mime=mime,
                    type=3,  # Cover (front)
                    desc='Cover',
                    data=image_data
                )
        
        # Apply album metadata if track-specific is missing
        if album_metadata:
            if 'title' not in track_metadata and 'title' in album_metadata:
                tags['TALB'] = TALB(encoding=3, text=album_metadata['title'])
            
            if 'artist' not in track_metadata and 'artist' in album_metadata:
                tags['TPE1'] = TPE1(encoding=3, text=album_metadata['artist'])
            
            if 'release_date' not in track_metadata and 'release_date' in album_metadata:
                year_match = re.search(r'(\d{4})', album_metadata['release_date'])
                if year_match:
                    tags['TYER'] = TYER(encoding=3, text=year_match.group(1))
        
        # Save the tags
        tags.save(mp3_file, v2_version=3)
        return True
    
    except Exception as e:
        logger.error(f"Error applying MP3 metadata to {mp3_file}: {str(e)}")
        return False

def apply_m4a_metadata(m4a_file, track_metadata, album_metadata, cover_art):
    """Apply metadata to an M4A file using mutagen."""
    try:
        from mutagen.mp4 import MP4, MP4Cover
        
        # Open the file
        tags = MP4(m4a_file)
        
        # Map track metadata to M4A tags
        if 'title' in track_metadata:
            tags['\xa9nam'] = [track_metadata['title']]
        
        if 'artist' in track_metadata:
            tags['\xa9ART'] = [track_metadata['artist']]
        
        if 'album_artist' in track_metadata:
            tags['aART'] = [track_metadata['album_artist']]
        
        if 'album' in track_metadata:
            tags['\xa9alb'] = [track_metadata['album']]
        
        # Track number and total
        if 'track_number' in track_metadata and 'total_tracks' in track_metadata:
            tags['trkn'] = [(int(track_metadata['track_number']), int(track_metadata['total_tracks']))]
        elif 'track_number' in track_metadata:
            tags['trkn'] = [(int(track_metadata['track_number']), 0)]
        
        # Disc number and total
        if 'disc_number' in track_metadata and 'total_discs' in track_metadata:
            tags['disk'] = [(int(track_metadata['disc_number']), int(track_metadata['total_discs']))]
        elif 'disc_number' in track_metadata:
            tags['disk'] = [(int(track_metadata['disc_number']), 0)]
        
        # Release date
        if 'release_date' in track_metadata:
            year_match = re.search(r'(\d{4})', track_metadata['release_date'])
            if year_match:
                tags['\xa9day'] = [year_match.group(1)]
        
        # Composer
        if 'composer' in track_metadata:
            tags['\xa9wrt'] = [track_metadata['composer']]
        
        # Copyright
        if 'copyright' in track_metadata:
            tags['cprt'] = [track_metadata['copyright']]
        
        # Lyrics
        if 'lyrics' in track_metadata:
            tags['\xa9lyr'] = [track_metadata['lyrics']]
        
        # Cover art
        if cover_art and os.path.exists(cover_art):
            with open(cover_art, 'rb') as img:
                image_data = img.read()
                cover_format = MP4Cover.FORMAT_JPEG if cover_art.lower().endswith(('.jpg', '.jpeg')) else MP4Cover.FORMAT_PNG
                tags['covr'] = [MP4Cover(image_data, cover_format)]
        
        # Apply album metadata if track-specific is missing
        if album_metadata:
            if 'title' not in track_metadata and 'title' in album_metadata:
                tags['\xa9alb'] = [album_metadata['title']]
            
            if 'artist' not in track_metadata and 'artist' in album_metadata:
                tags['\xa9ART'] = [album_metadata['artist']]
            
            if 'release_date' not in track_metadata and 'release_date' in album_metadata:
                year_match = re.search(r'(\d{4})', album_metadata['release_date'])
                if year_match:
                    tags['\xa9day'] = [year_match.group(1)]
        
        # Save the tags
        tags.save()
        return True
    
    except Exception as e:
        logger.error(f"Error applying M4A metadata to {m4a_file}: {str(e)}")
        return False

def apply_vorbis_metadata(vorbis_file, track_metadata, album_metadata, cover_art):
    """Apply metadata to an Ogg Vorbis or Opus file using mutagen."""
    try:
        from mutagen.oggvorbis import OggVorbis
        from mutagen.flac import Picture
        
        # Try loading as OggVorbis, but fall back to other types if needed
        try:
            tags = OggVorbis(vorbis_file)
        except:
            # For Opus files, use a different import
            from mutagen.oggopus import OggOpus
            tags = OggOpus(vorbis_file)
        
        # Map track metadata to Vorbis comments
        if 'title' in track_metadata:
            tags['TITLE'] = [track_metadata['title']]
        
        if 'artist' in track_metadata:
            tags['ARTIST'] = [track_metadata['artist']]
        
        if 'album_artist' in track_metadata:
            tags['ALBUMARTIST'] = [track_metadata['album_artist']]
        
        if 'album' in track_metadata:
            tags['ALBUM'] = [track_metadata['album']]
        
        # Track number and total
        if 'track_number' in track_metadata:
            if 'total_tracks' in track_metadata:
                tags['TRACKNUMBER'] = [f"{track_metadata['track_number']}/{track_metadata['total_tracks']}"]
            else:
                tags['TRACKNUMBER'] = [track_metadata['track_number']]
        
        # Disc number and total
        if 'disc_number' in track_metadata:
            if 'total_discs' in track_metadata:
                tags['DISCNUMBER'] = [f"{track_metadata['disc_number']}/{track_metadata['total_discs']}"]
            else:
                tags['DISCNUMBER'] = [track_metadata['disc_number']]
        
        # Release date
        if 'release_date' in track_metadata:
            year_match = re.search(r'(\d{4})', track_metadata['release_date'])
            if year_match:
                tags['DATE'] = [year_match.group(1)]
        
        # ISRC
        if 'isrc' in track_metadata:
            tags['ISRC'] = [track_metadata['isrc']]
        
        # Composer
        if 'composer' in track_metadata:
            tags['COMPOSER'] = [track_metadata['composer']]
        
        # Copyright
        if 'copyright' in track_metadata:
            tags['COPYRIGHT'] = [track_metadata['copyright']]
        
        # Lyrics
        if 'lyrics' in track_metadata:
            tags['LYRICS'] = [track_metadata['lyrics']]
        
        # Cover art for Vorbis files
        if cover_art and os.path.exists(cover_art):
            with open(cover_art, 'rb') as img:
                image_data = img.read()
                
                picture = Picture()
                picture.data = image_data
                picture.type = 3  # Cover (front)
                picture.desc = 'Cover'
                picture.mime = 'image/jpeg' if cover_art.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
                
                # Convert to base64 and add as METADATA_BLOCK_PICTURE
                picture_data = base64.b64encode(picture.write()).decode('ascii')
                tags['METADATA_BLOCK_PICTURE'] = [picture_data]
        
        # Apply album metadata if track-specific is missing
        if album_metadata:
            if 'title' not in track_metadata and 'title' in album_metadata:
                tags['ALBUM'] = [album_metadata['title']]
            
            if 'artist' not in track_metadata and 'artist' in album_metadata:
                tags['ARTIST'] = [album_metadata['artist']]
            
            if 'release_date' not in track_metadata and 'release_date' in album_metadata:
                year_match = re.search(r'(\d{4})', album_metadata['release_date'])
                if year_match:
                    tags['DATE'] = [year_match.group(1)]
        
        # Save the tags
        tags.save()
        return True
    
    except Exception as e:
        logger.error(f"Error applying Vorbis metadata to {vorbis_file}: {str(e)}")
        return False

def apply_flac_metadata(flac_file, track_metadata, album_metadata, cover_art):
    """Apply metadata to a FLAC file using mutagen."""
    try:
        from mutagen.flac import FLAC, Picture
        
        # Open the file
        tags = FLAC(flac_file)
        
        # Map track metadata to FLAC tags
        if 'title' in track_metadata:
            tags['TITLE'] = [track_metadata['title']]
        
        if 'artist' in track_metadata:
            tags['ARTIST'] = [track_metadata['artist']]
        
        if 'album_artist' in track_metadata:
            tags['ALBUMARTIST'] = [track_metadata['album_artist']]
        
        if 'album' in track_metadata:
            tags['ALBUM'] = [track_metadata['album']]
        
        # Track number and total
        if 'track_number' in track_metadata:
            if 'total_tracks' in track_metadata:
                tags['TRACKNUMBER'] = [f"{track_metadata['track_number']}/{track_metadata['total_tracks']}"]
            else:
                tags['TRACKNUMBER'] = [track_metadata['track_number']]
        
        # Disc number and total
        if 'disc_number' in track_metadata:
            if 'total_discs' in track_metadata:
                tags['DISCNUMBER'] = [f"{track_metadata['disc_number']}/{track_metadata['total_discs']}"]
            else:
                tags['DISCNUMBER'] = [track_metadata['disc_number']]
        
        # Release date
        if 'release_date' in track_metadata:
            year_match = re.search(r'(\d{4})', track_metadata['release_date'])
            if year_match:
                tags['DATE'] = [year_match.group(1)]
        
        # ISRC
        if 'isrc' in track_metadata:
            tags['ISRC'] = [track_metadata['isrc']]
        
        # Composer
        if 'composer' in track_metadata:
            tags['COMPOSER'] = [track_metadata['composer']]
        
        # Copyright
        if 'copyright' in track_metadata:
            tags['COPYRIGHT'] = [track_metadata['copyright']]
        
        # Lyrics
        if 'lyrics' in track_metadata:
            tags['LYRICS'] = [track_metadata['lyrics']]
        
        # Cover art for FLAC files
        if cover_art and os.path.exists(cover_art):
            with open(cover_art, 'rb') as img:
                image_data = img.read()
                
                picture = Picture()
                picture.data = image_data
                picture.type = 3  # Cover (front)
                picture.desc = 'Cover'
                picture.mime = 'image/jpeg' if cover_art.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
                
                # Clear existing pictures and add the new one
                tags.clear_pictures()
                tags.add_picture(picture)
        
        # Apply album metadata if track-specific is missing
        if album_metadata:
            if 'title' not in track_metadata and 'title' in album_metadata:
                tags['ALBUM'] = [album_metadata['title']]
            
            if 'artist' not in track_metadata and 'artist' in album_metadata:
                tags['ARTIST'] = [album_metadata['artist']]
            
            if 'release_date' not in track_metadata and 'release_date' in album_metadata:
                year_match = re.search(r'(\d{4})', album_metadata['release_date'])
                if year_match:
                    tags['DATE'] = [year_match.group(1)]
        
        # Save the tags
        tags.save()
        return True
    
    except Exception as e:
        logger.error(f"Error applying FLAC metadata to {flac_file}: {str(e)}")
        return False

def apply_metadata(output_file, output_format, track_metadata, album_metadata, cover_art, lyrics_mode):
    """Apply metadata to an audio file based on its format."""
    # Process lyrics according to mode
    if lyrics_mode != 'none' and 'lyrics' in track_metadata:
        if lyrics_mode == 'clean':
            # Strip timestamps
            track_metadata['lyrics'] = re.sub(r'\[\d+:\d+\.\d+\]\s*', '', track_metadata['lyrics'])
        # For 'timestamped' mode, leave as is
    
    # Apply metadata based on output format
    try:
        if output_format == 'mp3':
            return apply_mp3_metadata(output_file, track_metadata, album_metadata, cover_art)
        elif output_format in ['m4a', 'aac']:
            return apply_m4a_metadata(output_file, track_metadata, album_metadata, cover_art)
        elif output_format in ['ogg', 'opus']:
            return apply_vorbis_metadata(output_file, track_metadata, album_metadata, cover_art)
        elif output_format == 'flac':
            return apply_flac_metadata(output_file, track_metadata, album_metadata, cover_art)
        else:
            logger.warning(f"No metadata writer available for format: {output_format}")
            return False
    except Exception as e:
        logger.error(f"Error applying metadata to {output_file}: {str(e)}")
        return False
