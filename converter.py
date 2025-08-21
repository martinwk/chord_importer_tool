# <codecell>
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
from pathlib import Path
import re

class UGToChordProConverter:
    def __init__(self, url, verbose=False):
        self.driver = None
        self.url = url
        self.verbose = verbose
        self.ug_text = None
        self.chordpro = None

    def start_driver(self):
        """Initialize the Chrome driver"""
        if not self.driver:
            self.driver = webdriver.Chrome()

    def close_driver(self):
        """Close the Chrome driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def extract_ug_text(self):
        """Extract chord text from Ultimate Guitar URL"""
        self.start_driver()

        try:
            self.driver.get(self.url)

            # Wait for tab content to load
            content = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "pre, .js-tab-content, [data-content]"))
            )
            self.ug_text = content.text
            # return content.text

        except Exception as e:
            print(f"Error extracting UG text: {e}")
            return None

    def convert_with_ftes(self, text):
        """Convert text to ChordPro using FTES converter"""
        self.start_driver()

        try:
            self.driver.get("https://ultimate.ftes.de/")
            time.sleep(2)

            # Fill input textarea
            input_box = self.driver.find_element(By.TAG_NAME, "textarea")
            input_box.clear()
            input_box.send_keys(text)

            # Set dropdowns
            try:
                from_select = Select(self.driver.find_element(By.ID, "from"))
            except:
                from_select = Select(self.driver.find_elements(By.TAG_NAME, "select")[0])
            from_select.select_by_visible_text("Ultimate Guitar")

            try:
                to_select = Select(self.driver.find_element(By.ID, "to"))
            except:
                to_select = Select(self.driver.find_elements(By.TAG_NAME, "select")[1])
            to_select.select_by_visible_text("ChordPro")

            # Wait for conversion
            time.sleep(3)

            # Get output
            output_elements = self.driver.find_elements(By.TAG_NAME, "textarea")
            if len(output_elements) > 1:
                return output_elements[1].get_attribute("value")

            return None

        except Exception as e:
            print(f"Error converting with FTES: {e}")
            return None

    def convert_url_to_chordpro(self,):
        """Complete conversion from UG URL to ChordPro"""
        # Extract text from UG if not already done
        if not self.ug_text:
            self.extract_ug_text()
        if not self.ug_text:
            print("ug_text not succesfully extracted")
            return None

        # Convert to ChordPro
        self.chordpro = self.convert_with_ftes(self.ug_text)

    def extract_metadata(self,):
        """Extract metadata (title, artist, etc.) from Ultimate Guitar page"""
        self.start_driver()

        self.driver.get(self.url)
        time.sleep(2)

        self.metadata = {}

        # Extract title
        try:
            try:
                h1 = self.driver.find_element(By.TAG_NAME, "h1")
                self.metadata['title'] = h1.text.strip().replace("Chords", "").replace("Tab", "").strip()
            except Exception as e:
                print("Title extraction failed:", e)

            # Extract artist
            try:
                # Artist is often in a link above or near the title
                artist_elem = self.driver.find_element(By.XPATH, "//a[contains(@href, '/artist/')]")
                self.metadata['artist'] = artist_elem.text.strip()
            except Exception as e:
                print("Artist extraction failed:", e)

            # Extract difficulty/rating
            try:
                difficulty_elem = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Difficulty')]/following-sibling::*")
                self.metadata['difficulty'] = difficulty_elem.text.strip()
            except:
                pass

            # Extract key/capo/tuning
            try:
                info_spans = self.driver.find_elements(By.XPATH, "//span[contains(text(), 'Tuning') or contains(text(), 'Capo') or contains(text(), 'Key')]")
                for span in info_spans:
                    label = span.text.lower()
                    value = span.find_element(By.XPATH, "following-sibling::*[1]").text.strip()
                    if 'tuning' in label:
                        self.metadata['tuning'] = value
                    elif 'capo' in label:
                        self.metadata['capo'] = value
                    elif 'key' in label:
                        self.metadata['key'] = value
            except:
                pass

            # Extract tempo/BPM
            try:
                tempo_elem = self.driver.find_element(By.XPATH, "//span[contains(text(), 'BPM') or contains(text(), 'Tempo')]")
                self.metadata['tempo'] = tempo_elem.text.replace("BPM", "").replace("Tempo", "").strip()
            except:
                pass

        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {}

    def add_metadata_to_chordpro(self,):
        """Add metadata to the beginning of ChordPro content in proper format"""
        lines = self.chordpro.strip().split('\n')
        metadata_lines = []

        # Build ChordPro metadata block
        chordpro_tags = {
            'title': lambda v: f"{{title: {v}}}",
            'artist': lambda v: f"{{artist: {v}}}",
            'key': lambda v: f"{{key: {v}}}",
            'capo': lambda v: f"{{capo: {v}}}",
            'tempo': lambda v: f"{{tempo: {v}}}",
            'tuning': lambda v: f"{{meta: tuning {v}}}",
            'difficulty': lambda v: f"{{meta: difficulty {v}}}",
        }

        for key, formatter in chordpro_tags.items():
            value = self.metadata.get(key)
            if value:
                metadata_lines.append(formatter(value))

        # Remove any existing metadata tags to avoid duplication
        body_lines = [line for line in lines if not line.strip().startswith("{")]

        self.chordpro = '\n'.join(metadata_lines) + '\n\n' + '\n'.join(body_lines)

    def save_chordpro_to_file(self, parent_directory=r"C:\Users\mwkor\Dropbox\kerkband\Chordpro Immanuel"):
        """Save ChordPro text to a .cho file in artist/title.cho format using pathlib"""
        if not self.chordpro or not self.metadata:
            print("Missing chordpro text or metadata; cannot save.")
            return None

        # Fallbacks
        artist = self.metadata.get('artist', 'Unknown Artist').strip()
        title = self.metadata.get('title', 'Unknown Title').strip()

        # Sanitize folder and file names
        safe_artist = re.sub(r'[\\/*?:"<>|]', "_", artist)
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)

        # Build file path
        parent_path = Path(parent_directory)
        artist_folder = parent_path / safe_artist
        artist_folder.mkdir(parents=True, exist_ok=True)

        file_path = artist_folder / f"{safe_title}.cho"

        try:
            file_path.write_text(self.chordpro, encoding="utf-8")
            print(f"ChordPro file saved to: {file_path}")
            return str(file_path)
        except Exception as e:
            print(f"Error saving file: {e}")
            return None

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_driver()

# %%
def save_chordpro_from_uguitar(url="https://tabs.ultimate-guitar.com/tab/opwekking/80-ik-zal-opgaan-naar-gods-huis-chords-5462319",
                               parent_directory=r"C:\Users\mwkor\Dropbox\kerkband\Chordpro Immanuel"):
    # url = "https://tabs.ultimate-guitar.com/tab/reyer/laat-er-licht-zijn-chords-5024929?app_utm_campaign=Export2pdfDownload"
    # with UGToChordProConverter(url) as converter:
    converter = UGToChordProConverter(url)
    converter.convert_url_to_chordpro()
    # print(converter.chordpro)
    converter.extract_metadata()

    # %%
    converter.add_metadata_to_chordpro()
    converter.close_driver()

    # %%
    print(converter.chordpro)
    # %%
    converter.save_chordpro_to_file(parent_directory)
    converter.close_driver()

# %%
