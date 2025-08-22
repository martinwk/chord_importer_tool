# %%
#!/usr/bin/env python3
"""
ChordPro File Splitter for OnSong Exports
Splits a multi-song ChordPro file into individual song files with proper formatting.
"""

import re
import os
from typing import List, Tuple, Dict

def clean_filename(text: str) -> str:
    """Clean a string to be used as a filename."""
    # Remove special characters and replace spaces with hyphens
    cleaned = re.sub(r'[^\w\s-]', '', text)
    cleaned = re.sub(r'[-\s]+', '-', cleaned)
    return cleaned.strip('-').lower()

def is_section_identifier(line: str) -> bool:
    """Check if a line is a section identifier (with or without !)."""
    line = line.strip().lower()

    # Known section identifiers
    identifiers = [
        'chorus', 'verse', 'bridge', 'intro', 'interlude', 'pre-chorus',
        'post-chorus', 'tag', 'instrumental', 'outro', 'refrain'
    ]

    # Check if line starts with ! or is exactly one of our identifiers
    if line.startswith('!'):
        return True

    # Check if it's a standalone identifier (possibly with numbers)
    for identifier in identifiers:
        if line == identifier or line.startswith(identifier + ' '):
            return True

    return False

def parse_chordpro_identifiers(line: str) -> str:
    """Convert OnSong identifiers (with or without !) to proper ChordPro format."""
    line = line.strip()

    if not is_section_identifier(line):
        return line

    # Remove the ! prefix if present
    identifier = line[1:] if line.startswith('!') else line
    identifier_lower = identifier.lower()

    # Handle common cases
    if identifier_lower == 'chorus':
        return '{start_of_chorus}'
    elif identifier_lower.startswith('verse'):
        verse_num = identifier.split()[-1] if len(identifier.split()) > 1 else ''
        if verse_num:
            return f'{{start_of_verse: {identifier}}}'
        else:
            return '{start_of_verse}'
    elif identifier_lower == 'bridge':
        return '{start_of_bridge}'
    elif identifier_lower.startswith('pre-chorus'):
        return '{start_of_chorus: Pre-Chorus}'
    elif identifier_lower.startswith('post-chorus'):
        return '{start_of_chorus: Post-Chorus}'
    elif identifier_lower.startswith('intro'):
        return '{start_of_tab: Intro}'
    elif identifier_lower.startswith('interlude'):
        return '{start_of_tab: Interlude}'
    elif identifier_lower == 'tag':
        return '{start_of_chorus: Tag}'
    elif identifier_lower.startswith('instrumental'):
        return '{start_of_tab: Instrumental}'
    elif identifier_lower == 'outro':
        return '{start_of_tab: Outro}'
    elif identifier_lower == 'refrain':
        return '{start_of_chorus}'
    else:
        # Generic comment for unknown identifiers
        return f'{{comment: {identifier}}}'

def add_closing_tags(content: List[str]) -> List[str]:
    """Add appropriate closing tags for sections and clean up whitespace."""
    result = []
    open_sections = []

    for line in content:
        stripped = line.strip()

        # Skip empty lines temporarily - we'll handle them in cleanup
        if not stripped:
            result.append('')
            continue

        # Check if this line starts a new section
        if stripped.startswith('{start_of_'):
            # Close any open sections first
            while open_sections:
                section_type = open_sections.pop()
                result.append(f'{{end_of_{section_type}}}')

            # Add the new section
            result.append(stripped)

            # Extract section type
            if 'chorus' in stripped:
                open_sections.append('chorus')
            elif 'verse' in stripped:
                open_sections.append('verse')
            elif 'bridge' in stripped:
                open_sections.append('bridge')
            elif 'tab' in stripped:
                open_sections.append('tab')

        else:
            result.append(line.rstrip())  # Remove trailing whitespace

    # Close any remaining open sections
    while open_sections:
        section_type = open_sections.pop()
        result.append(f'{{end_of_{section_type}}}')

    return result

def clean_whitespace(lines: List[str]) -> List[str]:
    """Clean up excessive whitespace in the content while maintaining proper section spacing."""
    cleaned = []
    prev_was_empty = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        is_empty = not stripped
        is_section_start = stripped.startswith('{start_of_') or stripped.startswith('{comment:')
        is_section_end = stripped.startswith('{end_of_')

        # Skip double empty lines
        if is_empty and prev_was_empty:
            continue

        # Remove empty line directly after section start
        if is_empty and i > 0 and (lines[i-1].strip().startswith('{start_of_') or
                                    lines[i-1].strip().startswith('{comment:')):
            continue

        # Remove empty line directly before section end
        if is_section_end and cleaned and not cleaned[-1].strip():
            cleaned.pop()

        # Ensure there's a blank line before section start (if content precedes or previous section end)
        if is_section_start and cleaned and cleaned[-1].strip():
            # Always add blank line before section start, except after title/key/subtitle markers
            prev_line = cleaned[-1].strip()
            if not (prev_line.startswith('{title:') or prev_line.startswith('{key:') or
                   prev_line.startswith('{subtitle:') or prev_line.startswith('{artist:')):
                cleaned.append('')

        # Ensure there's a blank line after section end (if content follows)
        if is_section_end and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            # If next line has content and is not a section marker
            if (next_line and not (next_line.startswith('{start_of_') or
                                 next_line.startswith('{end_of_') or
                                 next_line.startswith('{comment:'))):
                cleaned.append(line)
                cleaned.append('')
                prev_was_empty = True
                continue

        cleaned.append(line)
        prev_was_empty = is_empty

    return cleaned

def extract_song_info(song_content: List[str]) -> Tuple[str, str]:
    """Extract title and subtitle/artist from song content."""
    title = "Unknown"
    artist = "Unknown"

    for line in song_content:
        line = line.strip()
        if line.startswith('{title:'):
            title = line[7:-1]  # Remove {title: and }
        elif line.startswith('{subtitle:'):
            artist = line[10:-1]  # Remove {subtitle: and }

    return clean_filename(artist), clean_filename(title)

def split_chordpro_file(file_path: str, output_dir: str = "songs") -> None:
    """Split a multi-song ChordPro file into individual song files."""

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by {new_song}
    songs = content.split('{new_song}')

    # Remove empty first element if file starts with {new_song}
    if songs[0].strip() == '':
        songs = songs[1:]

    print(f"Found {len(songs)} songs to process...")

    for i, song_content in enumerate(songs):
        if not song_content.strip():
            continue

        # Split into lines and process
        lines = song_content.split('\n')
        processed_lines = []

        for line in lines:
            if is_section_identifier(line):
                # Convert OnSong identifiers to ChordPro
                processed_line = parse_chordpro_identifiers(line)
                processed_lines.append(processed_line)
            else:
                processed_lines.append(line)

        # Add closing tags
        processed_lines = add_closing_tags(processed_lines)

        # Clean up whitespace
        processed_lines = clean_whitespace(processed_lines)

        # Extract song info for filename
        artist, title = extract_song_info(processed_lines)

        # Generate filename
        filename = f"{artist}-{title}.chopro"
        filepath = os.path.join(output_dir, filename)

        # Write song to file
        with open(filepath, 'w', encoding='utf-8') as f:
            for line in processed_lines:
                f.write(line + '\n' if not line.endswith('\n') else line)

        print(f"Created: {filename}")

def main(input_file = "Dienst zondag 24-08-2025.chopro",  # Input file name,
         output_directory = "split_songs"  # Output directory
         ):
    """Main function - Minimal Working Example"""

    try:
        split_chordpro_file(input_file, output_directory)
        print(f"\nSuccessfully split songs into '{output_directory}' directory!")

    except FileNotFoundError:
        print(f"Error: Could not find input file '{input_file}'")
        print("Please make sure the file exists in the current directory.")

    except Exception as e:
        print(f"Error processing file: {e}")

# %%
main()

# %%
