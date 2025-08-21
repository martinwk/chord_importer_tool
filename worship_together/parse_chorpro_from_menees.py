# from https://www.worshiptogether.com/songs/the-joy-the-belonging-co/ copy the
# text in https://chords.menees.com/ then copy then download that text and parse it here
# Next steps:
# - copy the text from worship together and use let that copied text be parsed
#   - somehow add the artist and title
#   - recognice all verses intro chorus pre-chorus vamp bridge (including followed integer) and put squared brackets around it
# - copy that text, go to menees and paste it, convert it, copy the result
# - used that result with this script below

# <markdowncell>
# i have a file in cho format and i want to load it in python and want to remove the linebreak for every line that ends with a word (not a chord). write this new text to an output file. use the title and artist in the cho file to create a output file name artist-title.cho . make a minimal amount of code

# Looking at this task, I'll create a minimal Python script that processes CHO (ChordPro) files. CHO files typically contain lyrics with chord annotations, where lines ending with chords (usually in brackets) should keep their line breaks, but lines ending with words (lyrics) should have line breaks removed for better formatting.

# This minimal script:

#     Reads the CHO file and processes it line by line
#     Extracts title and artist from {title:} or {t:} and {artist:} or {a:} directives
#     Removes line breaks from lines ending with words (not chords in brackets ] or directives in braces })
#     Creates output filename as artist-title.cho with cleaned characters
#     Writes the processed content to the new file

# Usage:
# bash

# python script.py input.cho

# The script assumes that:

#     Chord lines end with ] (chord brackets)
#     Directive lines end with } (ChordPro directives)
#     Lyric lines end with regular words and should have their line breaks removed

# Lines ending with words get a space added instead of a newline, so lyrics flow toge

# <codecell>
import re
import sys

def process_cho_file(input_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    title = artist = ""
    processed_lines = []

    for line in lines:
        line = line.rstrip('\n\r')

        # Extract title and artist
        if line.startswith('{title:') or line.startswith('{t:'):
            title = re.search(r'{t(?:itle)?:\s*(.+?)}', line).group(1)
        elif line.startswith('{artist:') or line.startswith('{a:'):
            artist = re.search(r'{a(?:rtist)?:\s*(.+?)}', line).group(1)

        # Check if line ends with a word (not chord or directive)
        if line and not line.endswith('}') and not re.search(r'\]$', line) and not line.endswith('/') and not line.endswith('|'):
            processed_lines.append(line + ' ')  # Add space instead of newline
        else:
            processed_lines.append(line + '\n')

    # Remove consecutive whitelines and whitelines not near directives
    final_lines = []
    i = 0
    while i < len(processed_lines):
        line = processed_lines[i].strip()

        # If it's an empty line
        if not line:
            # Skip consecutive empty lines
            while i + 1 < len(processed_lines) and not processed_lines[i + 1].strip():
                i += 1

            # Check if empty line is preceded or followed by a directive
            prev_directive = i > 0 and processed_lines[i-1].strip().startswith('{') and processed_lines[i-1].strip().endswith('}')
            next_directive = i + 1 < len(processed_lines) and processed_lines[i+1].strip().startswith('{') and processed_lines[i+1].strip().endswith('}')

            # Don't allow whiteline after directive containing "start_of"
            prev_start_of = i > 0 and 'start_of' in processed_lines[i-1].strip().lower()

            if (prev_directive or next_directive) and not prev_start_of:
                final_lines.append('\n')
        else:
            final_lines.append(processed_lines[i])

        i += 1

    # Create output filename
    output_file = f"{artist}-{title}.cho" if artist and title else "output.cho"
    output_file = re.sub(r'[^\w\-_.]', '_', output_file)  # Clean filename

    # Write processed content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(''.join(final_lines))

    print(f"Processed file saved as: {output_file}")

# # Usage
# if len(sys.argv) != 2:
#     print("Usage: python script.py input.cho")
#     sys.exit(1)

# process_cho_file(sys.argv[1])
# %%
process_cho_file('The Joy.cho')
# %%
