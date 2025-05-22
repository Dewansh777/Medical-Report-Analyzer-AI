import fitz # PyMuPDF
import os
import io
from PIL import Image
import streamlit as st # For feedback/errors

# Define the temporary directory for images
TEMP_IMAGE_DIR = os.path.join("data", "temp")
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True) # Ensure directory exists

# Helper function to clean temp dir (optional, but good practice)
def clear_temp_images():
    for filename in os.listdir(TEMP_IMAGE_DIR):
        file_path = os.path.join(TEMP_IMAGE_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting temp file {file_path}: {e}")


class PDFParserAgent:
    """
    Agent responsible for parsing the PDF file, extracting text,
    and identifying/extracting images. Uses context manager for file handling.
    """
    def __init__(self):
        pass

    def extract_text_and_images(self, pdf_path):
        """
        Opens a PDF and extracts text and images page by page using a context manager.

        Args:
            pdf_path (str): Path to the PDF file.

        Returns:
            dict: A dictionary containing:
                  'full_text': Concatenated text from all pages.
                  'images': A list of dictionaries, each with 'page_num' and 'image_bytes'.
                  'pages_text': A list of text content per page.
            Returns None if an error occurs.
        """
        full_text = ""
        pages_text = []
        images_data = []
        extracted_image_count = 0
        page_count = 0 # Initialize page count
        current_page_num_for_log = 0 # Initialize page number for logging

        try:
            # Verify the temporary file exists before trying to open it
            if not os.path.exists(pdf_path):
                 st.error(f"Temporary PDF file not found at path: {pdf_path}")
                 return None
            if os.path.getsize(pdf_path) == 0:
                 st.error(f"Temporary PDF file is empty (0 bytes): {pdf_path}")
                 return None
            st.write(f"Attempting to open PDF: {pdf_path}")

            # Use context manager for reliable opening and closing
            with fitz.open(pdf_path) as doc:
                page_count = len(doc)
                st.write(f"Successfully opened PDF. Number of pages: {page_count}") # Debug print

                for page_num in range(page_count):
                    current_page_num_for_log = page_num + 1 # Track current page for logging
                    st.write(f"Processing page {current_page_num_for_log}/{page_count}...") # Debug print
                    page = doc.load_page(page_num)

                    # 1. Extract Text
                    page_text = page.get_text("text")
                    full_text += f"\n--- Page {current_page_num_for_log} ---\n{page_text}\n"
                    pages_text.append(page_text)
                    # st.write(f"  - Text extracted (length: {len(page_text)})") # Optional detailed log

                    # 2. Extract Images
                    image_list = page.get_images(full=True)
                    # st.write(f"  - Found {len(image_list)} potential image references on page.") # Optional detailed log
                    if image_list: # Only proceed if there are images
                        for img_index, img_info in enumerate(image_list):
                            xref = img_info[0]
                            try:
                                # Use doc.extract_image within the loop
                                base_image = doc.extract_image(xref)
                                if base_image and base_image.get("image"): # Check if image extraction was successful and got bytes
                                    image_bytes = base_image["image"]
                                    images_data.append({
                                        "page_num": current_page_num_for_log,
                                        "image_bytes": image_bytes,
                                        "index_on_page": img_index
                                    })
                                    extracted_image_count += 1
                                    # st.write(f"    - Successfully extracted image {img_index + 1} (xref {xref})") # Optional detailed log
                                else:
                                    st.warning(f"    - Could not extract valid image data for xref {xref} on page {current_page_num_for_log}")
                            except Exception as img_e:
                                 st.warning(f"    - Error extracting image xref {xref} on page {current_page_num_for_log}: {img_e}")

                st.write("Finished processing all pages.") # Debug print

            # No need for explicit doc.close() when using 'with' statement
            st.write("Document automatically closed by context manager.") # Debug print
            st.info(f"Extracted text from {page_count} pages and found {extracted_image_count} images.")

            return {
                "full_text": full_text.strip(),
                "images": images_data,
                "pages_text": pages_text
            }

        # --- More Specific Error Handling ---
        # Catch specific fitz/PyMuPDF errors first
        except fitz.fitz.FitzError as fe:
             st.error(f"PyMuPDF Error parsing PDF: {fe}. Occurred around page: {current_page_num_for_log if current_page_num_for_log > 0 else 'N/A (likely during open or initial load)'}")
             return None
        # Catch potential errors related to file access/permissions
        except IOError as ioe:
             st.error(f"File IO Error accessing PDF '{pdf_path}': {ioe}")
             return None
        # Catch other general exceptions
        except Exception as e:
            st.error(f"General Error parsing PDF: {e}. Occurred around page: {current_page_num_for_log if current_page_num_for_log > 0 else 'N/A (likely during open or initial load)'}")
            # No need to manually close doc here, 'with' handles it.
            return None