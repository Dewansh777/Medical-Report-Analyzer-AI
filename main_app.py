import streamlit as st
from agents.parser_agent import PDFParserAgent, clear_temp_images
from agents.analyzer_agent import AnalyzerAgent
from utils.helpers import load_api_key
import os
import google.generativeai as genai

# --- Page Configuration ---
st.set_page_config(page_title="Medical Report Analyzer AI", layout="wide")

# --- Load API Key ---
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)
# --- Initialize Agents ---
parser = PDFParserAgent()
analyzer = AnalyzerAgent()

# --- UI Elements ---
st.title("🩺 Multimodal Medical Report Analyzer AI")
st.markdown("""
Upload a medical report (PDF format). The AI will attempt to extract information,
analyze numerical data and images (if any), and provide a general interpretation.

**Disclaimer:** This tool is for informational purposes ONLY and is NOT a substitute
for professional medical advice, diagnosis, or treatment. Always consult a doctor.
The AI may make mistakes or misinterpret information. Verify results with a healthcare professional.
""")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    # Clear previous temporary files before processing new file (optional)
    clear_temp_images()

    # Save uploaded file temporarily
    temp_pdf_path = os.path.join("data", "temp", uploaded_file.name)
    with open(temp_pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.info(f"Processing '{uploaded_file.name}'...")

    # --- Agent Workflow ---
    with st.spinner("Parsing PDF and extracting data..."):
        extracted_data = parser.extract_text_and_images(temp_pdf_path)

    if extracted_data:
        # Display extracted images (optional, for verification)
        # if extracted_data.get("images"):
        #     st.subheader("Extracted Images (for reference):")
        #     cols = st.columns(4) # Adjust number of columns as needed
        #     for i, img_data in enumerate(extracted_data["images"]):
        #          with cols[i % 4]:
        #              st.image(img_data["image_bytes"], caption=f"Page {img_data['page_num']}, Img {img_data['index_on_page']+1}", use_container_width=True)


        with st.spinner("Analyzing report content with AI Agents... Please wait."):
            analysis_results = analyzer.analyze_report(extracted_data)

        if analysis_results:
            st.subheader("📊 AI Analysis Results:")

            # Display Initial Extraction (if generated)
            if 'initial_extraction' in analysis_results:
                 with st.expander("View Initial Data Extraction & Text Summary"):
                     st.markdown(analysis_results['initial_extraction'])

            # Display Final Analysis
            if 'final_analysis' in analysis_results:
                # with pd.read_csv('open.xml',clear=True,expand=False,sep='/t'):

                st.markdown("---")
                st.markdown("### Overall Interpretation & Suggestions")
                st.markdown(analysis_results['final_analysis'])
            else:
                st.error("Could not generate the final analysis.")

            st.markdown("---")
            st.warning("**Reminder:** Always discuss these findings with your doctor for accurate interpretation and guidance.")

        else:
            st.error("Analysis failed. Could not process the extracted data.")

    else:
        st.error("Failed to parse the PDF file.")

    # Clean up the temporary PDF file
    try:
        os.remove(temp_pdf_path)
    except Exception as e:
        st.warning(f"Could not remove temporary file {temp_pdf_path}: {e}")

else:
    st.info("Please upload a PDF report to begin analysis.")