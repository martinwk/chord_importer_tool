#%%
import PyPDF2

with open("opwv0566ga.pdf", "rb") as pdf_file:
    read_pdf = PyPDF2.PdfReader(pdf_file)
    number_of_pages = len(read_pdf.pages)
    page = read_pdf.pages[0]
    page_content = page.extract_text()
print(page_content)

# %%
#!/usr/bin/env python3
#!/usr/bin/env python3
"""
PDF to ChordPro Format Converter for Opwekking Song Format
Converts extracted PDF text from PyPDF2 with embedded chords to ChordPro format.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional

class OpwekkingChordProConverter:
    def __init__(self):
        # Enhanced chord pattern for complex chords like Bb2, C/D, F/A, etc.
        self.chord_pattern = re.compile(r'\b[A-G][#b]?(?:sus|maj|min|m|M|add|dim|aug|\d)*(?:/[A-G][#b]?)?\b')

    def extract_metadata(self, text: str) -> Tuple[dict, str]:
        """
        Extract metadata from the beginning and end of the text.
        Returns (metadata_dict, remaining_text)
        """
        lines = text.split('\n')
        metadata = {}
        content_start = 0

        # Extract title and BPM from first lines
        if lines and re.match(r'^\d+\s+', lines[0]):
            # First line like "566 Machtig Heer"
            title_line = lines[0].strip()
            parts = title_line.split(' ', 1)
            if len(parts) == 2:
                metadata['number'] = parts[0]
                metadata['title'] = parts[1]
            content_start = 1

        if len(lines) > content_start and 'bpm' in lines[content_start].lower():
            metadata['tempo'] = lines[content_start].strip()
            content_start += 1

        # Extract copyright info from the end
        copyright_pattern = r'Oorspr\. titel:|Tekst & muziek:|Ned\. tekst:|©'
        for i, line in enumerate(lines):
            if re.search(copyright_pattern, line):
                # Everything from this line onwards is metadata
                metadata['copyright'] = '\n'.join(lines[i:])
                # Remove copyright from main content
                remaining_text = '\n'.join(lines[content_start:i])
                return metadata, remaining_text

        remaining_text = '\n'.join(lines[content_start:])
        return metadata, remaining_text

    def identify_chord_positions(self, text: str) -> List[Tuple[int, str]]:
        """
        Find all chord positions in the text.
        Returns list of (position, chord) tuples.
        """
        chord_positions = []
        for match in self.chord_pattern.finditer(text):
            chord = match.group()
            # Skip if it's likely part of a Dutch word rather than a chord
            if self.is_likely_chord(chord, text, match.start(), match.end()):
                chord_positions.append((match.start(), chord))
        return chord_positions

    def is_likely_chord(self, chord: str, text: str, start: int, end: int) -> bool:
        """
        Determine if a matched pattern is actually a chord vs part of a Dutch word.
        """
        # Check context around the chord
        before = text[max(0, start-2):start]
        after = text[end:end+2]

        # If surrounded by lowercase letters, probably part of a word
        if before and before[-1].islower() and after and after[0].islower():
            return False

        # Common Dutch words that might contain chord-like patterns
        dutch_words = ['dat', 'aan', 'een', 'van', 'met', 'als', 'bij', 'dit', 'hij', 'zij']

        # Check if it's part of a longer Dutch word
        word_start = start
        while word_start > 0 and text[word_start-1].isalpha():
            word_start -= 1
        word_end = end
        while word_end < len(text) and text[word_end].isalpha():
            word_end += 1

        full_word = text[word_start:word_end].lower()
        if full_word in dutch_words:
            return False

        return True

    def separate_chords_from_lyrics(self, text: str) -> str:
        """
        Main function to separate embedded chords from lyrics and format as ChordPro.
        """
        # Find all chord positions
        chord_positions = self.identify_chord_positions(text)

        if not chord_positions:
            return text

        # Sort by position (reverse order for safe removal)
        chord_positions.sort(reverse=True)

        # Remove chords from text and build chord-lyric mapping
        result_text = text
        chord_insertions = []  # (position_after_removal, chord)

        for pos, chord in chord_positions:
            # Calculate the position in lyrics after previous chord removals
            lyrics_pos = pos
            for prev_pos, prev_chord in reversed(chord_positions):
                if prev_pos > pos:
                    lyrics_pos -= len(prev_chord)

            # Remove chord from text
            result_text = result_text[:pos] + result_text[pos + len(chord):]

            # Store where to insert chord in ChordPro format
            chord_insertions.append((lyrics_pos, chord))

        # Sort insertions by position
        chord_insertions.sort()

        # Insert chords in ChordPro format
        for lyrics_pos, chord in reversed(chord_insertions):
            # Find the best insertion point (start of word if possible)
            insert_pos = lyrics_pos
            # Don't split words - move to start of word
            while insert_pos > 0 and result_text[insert_pos-1].isalpha():
                insert_pos -= 1

            chord_tag = f"[{chord}]"
            result_text = result_text[:insert_pos] + chord_tag + result_text[insert_pos:]

        return result_text

    def format_sections(self, text: str) -> str:
        """
        Format different sections (Intro, Refrein, Coda, etc.)
        """
        # Replace section headers
        text = re.sub(r'\bIntro:\s*', '\n{start_of_chorus}\nIntro:\n', text)
        text = re.sub(r'\bRefrein:\s*', '\n{start_of_chorus}\nRefrein:\n', text)
        text = re.sub(r'\bRefrein 2x:\s*', '\n{start_of_chorus}\nRefrein (2x):\n', text)
        text = re.sub(r'\bCoda:\s*', '\n{start_of_chorus}\nCoda:\n', text)
        text = re.sub(r'\bVers \d+:\s*', '\n{start_of_verse}\nVers:\n', text)

        return text

    def clean_and_format_lyrics(self, text: str) -> str:
        """
        Clean up spacing and formatting issues from PDF extraction.
        """
        # Fix spacing issues
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single space
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines to double

        # Add line breaks before chord progressions like |F/A |Bb2 |
        text = re.sub(r'\|([A-G][^|]*)\|', r'\n|\1|', text)

        # Format chord progressions
        text = re.sub(r'\|([^|]+)\|', r'[\1]', text)

        # Clean up extra spaces around brackets
        text = re.sub(r'\s*\[\s*([^\]]+)\s*\]\s*', r'[\1]', text)

        return text.strip()

    def convert_to_chordpro(self, pdf_text: str) -> str:
        """
        Main conversion function.
        """
        # Extract metadata
        metadata, content = self.extract_metadata(pdf_text)

        # Start building ChordPro output
        result = []

        # Add metadata
        if 'title' in metadata:
            result.append(f"{{t: {metadata['title']}}}")
        if 'tempo' in metadata:
            result.append(f"{{tempo: {metadata['tempo']}}}")

        result.append("")  # Empty line after metadata

        # Process main content
        content = self.separate_chords_from_lyrics(content)
        content = self.format_sections(content)
        content = self.clean_and_format_lyrics(content)

        result.append(content)

        # Add copyright information
        if 'copyright' in metadata:
            result.append("")
            result.append("{c: " + metadata['copyright'].replace('\n', ' | ') + "}")

        return '\n'.join(result)

def convert_opwekking_pdf(pdf_file_path: str, output_file: str = None) -> str:
    """
    Convenience function to convert an Opwekking PDF file to ChordPro format.
    """
    try:
        import PyPDF2
    except ImportError:
        print("PyPDF2 is required. Install with: pip install PyPDF2")
        return ""

    pdf_path = Path(pdf_file_path)

    # Check if PDF file exists
    if not pdf_path.exists():
        print(f"Error: PDF file '{pdf_path}' not found.")
        return ""

    # Extract text from PDF
    with pdf_path.open("rb") as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        page = reader.pages[0]  # Assuming single page
        extracted_text = page.extract_text()

    # Convert to ChordPro
    converter = OpwekkingChordProConverter()
    chordpro_result = converter.convert_to_chordpro(extracted_text)

    # Save to file if specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)  # Create directories if needed
        output_path.write_text(chordpro_result, encoding='utf-8')
        print(f"ChordPro file saved as: {output_path}")

    return chordpro_result
# %%

def main():
    """
    Main function - can be called with PDF file or text content.
    """
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python converter.py opwv0566ga.pdf [output.cho]")
        print("  python converter.py --text 'extracted_text_here' [output.cho]")
        return

    converter = OpwekkingChordProConverter()

    if sys.argv[1] == '--text':
        # Direct text input
        if len(sys.argv) < 3:
            print("Please provide text after --text flag")
            return
        text_input = sys.argv[2]
        result = converter.convert_to_chordpro(text_input)
    else:
        # PDF file input
        pdf_path = Path(sys.argv[1])
        if not pdf_path.exists():
            print(f"Error: PDF file '{pdf_path}' not found.")
            return
        result = convert_opwekking_pdf(str(pdf_path))

    # Output
    if len(sys.argv) >= 3 and sys.argv[1] != '--text':
        output_file = sys.argv[2]
    elif len(sys.argv) >= 4 and sys.argv[1] == '--text':
        output_file = sys.argv[3]
    else:
        output_file = None

    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)  # Create directories if needed
        output_path.write_text(result, encoding='utf-8')
        print(f"ChordPro file saved as: {output_path}")
    else:
        print("ChordPro Output:")
        print("-" * 50)
        print(result)

# Example usage with your specific text
def test_with_sample():
    sample_text = """566 Machtig Heer
76 bpm
Intro:
|F/A |Bb2 |Bb2/C |C Am7 |
Ik verlang naar uw aanBb2wezigC/DheidDm in alles wat ik Bb2doe.Am7
Dat uw Geest mij op mijn Gm7wegen leidt,F/A wijd ik heel mijn Bbleven aan U Bb/Ctoe. F Am7

Oorspr. titel: Lord, I long to see You glorified (Lord of all)
Tekst & muziek: Steve McPherson
© 1996 Hillsong Music Publishing"""

    converter = OpwekkingChordProConverter()
    result = converter.convert_to_chordpro(sample_text)
    print("Sample conversion:")
    print(result)

if __name__ == "__main__":
    main()
# %%
pdf_file = Path(r"C:\Users\mwkor\Repositories\chord_importer_tool\opwv0566ga.pdf")
convert_opwekking_pdf(pdf_file, "opw566.cho")
# %%
