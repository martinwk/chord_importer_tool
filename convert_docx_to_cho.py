# %%
#!/usr/bin/env python3
"""
Basic DOCX Text Extractor
Extracts text from a DOCX file as if it was copied to clipboard.
"""

from pathlib import Path
import sys

def extract_text_from_docx(docx_path):
    """
    Extract plain text from a DOCX file.
    Returns text as if it was copied to clipboard.
    """
    try:
        from docx import Document
    except ImportError:
        print("python-docx is required. Install with: pip install python-docx")
        return ""

    # Load the document
    doc_path = Path(docx_path)
    if not doc_path.exists():
        print(f"Error: File '{doc_path}' not found.")
        return ""

    try:
        doc = Document(doc_path)

        # Extract text from all paragraphs
        text_content = []
        for paragraph in doc.paragraphs:
            text_content.append(paragraph.text)

        # Join with newlines to preserve paragraph structure
        return '\n'.join(text_content)

    except Exception as e:
        print(f"Error reading DOCX file: {e}")
        return ""

def main():
    """
    Main function to extract text from DOCX file.
    """
    if len(sys.argv) < 2:
        print("Usage: python docx_extractor.py <input.docx> [output.txt]")
        return

    input_file = sys.argv[1]

    # Extract text
    extracted_text = extract_text_from_docx(input_file)

    if not extracted_text:
        print("No text extracted or error occurred.")
        return

    # Output to file or console
    if len(sys.argv) >= 3:
        output_file = Path(sys.argv[2])
        output_file.write_text(extracted_text, encoding='utf-8')
        print(f"Text saved to: {output_file}")
    else:
        print("Extracted Text:")
        print("-" * 50)
        print(extracted_text)

# Example usage function
def test_extraction():
    """
    Test function - replace 'test.docx' with your actual file
    """
    text = extract_text_from_docx('test.docx')
    print("Extracted text:")
    print(text)

if __name__ == "__main__":
    main()

# %%
docx_file =Path(r"C:\Users\mwkor\Downloads\Praise.docx")
text = extract_text_from_docx(docx_file)
print("Extracted text:")
print(text)
# <markdowncell>
# # Test Chordconverter
# ## Code
# %%
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time

class MeneesChordConverter:
    def __init__(self, headless=True):
        """
        Initialize the converter with Chrome WebDriver
        Set headless=False if you want to see the browser window
        """
        self.headless = headless
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        try:
            # Try to create driver (you may need to install chromedriver)
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            print("Make sure you have Chrome and chromedriver installed")
            print("Install with: pip install selenium")
            print("Download chromedriver from: https://chromedriver.chromium.org/")
            raise

    def convert_to_chordpro(self, input_text):
        """
        Convert text to ChordPro format using chords.menees.com
        """
        try:
            # Navigate to the website
            print("Loading chords.menees.com...")
            self.driver.get("https://chords.menees.com/")

            # Wait for page to load
            wait = WebDriverWait(self.driver, 15)

            # Look for input textarea (try common selectors)
            input_selectors = [
                "textarea",
                "#input",
                ".input",
                "[placeholder*='paste']",
                "[placeholder*='text']",
                "textarea[rows]"
            ]

            input_element = None
            for selector in input_selectors:
                try:
                    input_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    print(f"Found input element with selector: {selector}")
                    break
                except:
                    continue

            if not input_element:
                # Try to find any textarea
                textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
                if textareas:
                    input_element = textareas[0]
                    print("Found textarea element")
                else:
                    raise Exception("Could not find input textarea")

            # Clear and enter the text
            print("Entering text...")
            input_element.clear()
            input_element.send_keys(input_text)

            # Look for convert button
            convert_selectors = [
                "button[onclick*='convert']",
                "input[value*='Convert']",
                "button:contains('Convert')",
                "#convert",
                ".convert",
                "button[type='submit']",
                "input[type='submit']"
            ]

            convert_button = None
            for selector in convert_selectors:
                try:
                    convert_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"Found convert button with selector: {selector}")
                    break
                except:
                    continue

            if not convert_button:
                # Try to find any button
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                if buttons:
                    convert_button = buttons[0]
                    print("Found button element")
                else:
                    raise Exception("Could not find convert button")

            # Click the convert button
            print("Clicking convert button...")
            convert_button.click()

            # Wait a moment for conversion
            time.sleep(2)

            # Look for output/result area
            output_selectors = [
                "#output",
                ".output",
                "#result",
                ".result",
                "textarea:nth-of-type(2)",  # Second textarea
                ".right-pane textarea",
                "[readonly]"
            ]

            output_element = None
            for selector in output_selectors:
                try:
                    output_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if output_element.get_attribute("value") or output_element.text:
                        print(f"Found output element with selector: {selector}")
                        break
                except:
                    continue

            if not output_element:
                # Try to find the second textarea or any textarea with content
                textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
                for i, textarea in enumerate(textareas):
                    content = textarea.get_attribute("value") or textarea.text
                    if content and content.strip() != input_text.strip():
                        output_element = textarea
                        print(f"Found output in textarea #{i}")
                        break

            if output_element:
                # Get the converted text
                result = output_element.get_attribute("value") or output_element.text
                if result and result.strip():
                    return result.strip()
                else:
                    return "No result found in output element"
            else:
                # Last resort: get page source for debugging
                return f"Could not find output element. Page title: {self.driver.title}"

        except Exception as e:
            return f"Error during conversion: {str(e)}"

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Minimal working example
def main():
    # Sample chord text to convert
    sample_text = """G                C
Amazing grace, how sweet the sound
G                D
That saved a wretch like me
G                C
I once was lost, but now I'm found
G        D        G
Was blind but now I see"""

    print("Starting ChordPro conversion...")
    print("Sample input:")
    print(sample_text)
    print("-" * 50)

    # Use context manager to ensure browser closes
    try:
        with MeneesChordConverter(headless=True) as converter:
            result = converter.convert_to_chordpro(sample_text)
            print("Conversion result:")
            print(result)
    except Exception as e:
        print(f"Failed to initialize converter: {e}")

if __name__ == "__main__":
    main()
# %%
