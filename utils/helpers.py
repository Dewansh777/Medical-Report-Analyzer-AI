import google.generativeai as genai
import os
from dotenv import load_dotenv
import streamlit as st
from PIL import Image # Import PIL for image handling
import io # Import io for image bytes handling

# --- Configuration ---
def load_api_key():
    """Loads the Google API key from .env file."""
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("API key not found. Please set GOOGLE_API_KEY in your .env file.")
        st.stop()
    genai.configure(api_key=api_key)
    return api_key

# --- Gemini API Interaction ---
# Use Streamlit's caching to avoid redundant API calls for the same input
@st.cache_data(show_spinner=False) # Use Streamlit's caching
def call_gemini_text(prompt, model_name="gemini-1.5-flash"): # Using 1.5 Flash as a good default
    """Calls the Gemini API for text generation."""
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error calling Gemini API (Text): {e}")
        return None

@st.cache_data(show_spinner=False) # Use Streamlit's caching
def call_gemini_vision(prompt, image_bytes_list, model_name="gemini-1.5-flash"): # Using 1.5 Flash as it handles vision
    """Calls the Gemini API for vision (multimodal) tasks."""
    if not image_bytes_list:
        return call_gemini_text(prompt, model_name) # Fallback to text if no images

    try:
        model = genai.GenerativeModel(model_name)

        # Prepare image parts for the API
        image_parts = []
        for img_bytes in image_bytes_list:
            try:
                # Re-open the image bytes to ensure correct processing with PIL
                img = Image.open(io.BytesIO(img_bytes))

                # Convert to RGB to handle potential palette/alpha issues that might affect saving to JPEG
                if img.mode in ('P', 'RGBA'):
                    img = img.convert('RGB')

                # Save the image to a bytes buffer in JPEG format
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG') # Explicitly save as JPEG
                img_byte_arr = img_byte_arr.getvalue() # Get the bytes

                image_parts.append({
                    "mime_type": "image/jpeg", # Correct MIME type for JPEG
                    "data": img_byte_arr
                })
            except Exception as img_e:
                st.warning(f"Could not process and re-format an image for API call: {img_e}")
                continue # Skip problematic images
        if not image_parts: # If all images failed processing
             st.warning("No valid images could be processed for vision analysis.")
             return call_gemini_text(prompt, model_name) # Fallback to text

        # Combine prompt and images
        content = [prompt] + image_parts
        response = model.generate_content(content)
        return response.text

    except Exception as e:
        st.error(f"Error calling Gemini API (Vision): {e}")
        return None

# --- Add other utility functions as needed ---
# E.g., functions for specific text cleaning, data formatting, etc.