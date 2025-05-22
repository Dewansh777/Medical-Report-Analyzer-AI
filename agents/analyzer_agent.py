from utils.helpers import call_gemini_text, call_gemini_vision
import streamlit as st

class AnalyzerAgent:
    """
    Agent responsible for analyzing the extracted text and images,
    interpreting results, suggesting potential conditions, and offering general advice.
    """
    def __init__(self):
        # Could load knowledge bases or configure models here
        pass

    def analyze_report(self, extracted_data):
        """
        Analyzes the extracted PDF data using Gemini models.

        Args:
            extracted_data (dict): The dictionary returned by the ParserAgent.

        Returns:
            dict: A dictionary containing the analysis results.
                  Returns None if analysis fails.
        """
        if not extracted_data:
            st.error("No data provided to Analyzer Agent.")
            return None

        full_text = extracted_data.get("full_text", "")
        images = extracted_data.get("images", [])
        image_bytes_list = [img['image_bytes'] for img in images] # Get list of image bytes

        if not full_text and not images:
            st.warning("PDF contained no extractable text or images.")
            return None

        st.info("Analyzing report data with AI...")

        # --- Construct Prompts ---

        # 1. Prompt for extracting structured information and initial analysis (Text Focus)
        # This prompt tries to get Gemini to identify key tests and findings first.
        # Adapt this prompt based on the typical structure of your reports.
        extraction_prompt = f"""
        Analyze the following medical report text extracted from a PDF.
        Identify key sections (e.g., Blood Report, Lipid Profile, Liver Function, Imaging Findings).
        For each numerical test result found (like blood counts, cholesterol levels, enzyme levels, etc.), extract:
        - Test Name
        - Value
        - Unit (if available)
        - Reference Range (if available in the text)
        Summarize any textual findings, especially from imaging sections if present in the text.

        Extracted Text:
        ---
        {full_text}
        ---

        Output the findings in a structured manner (e.g., using Markdown lists or sections).
        """

        # 2. Prompt for Overall Analysis and Synthesis (Multimodal if images exist)
        # This prompt will be used *after* the initial extraction/summary, or combined
        # with the image analysis if images are present.
        synthesis_prompt = f"""
        You are an AI assistant analyzing medical report data.
        Based *only* on the information provided below (extracted text summary and any associated images), perform the following:

        1.  **Summarize Key Findings:** Briefly list the most significant results (both numerical and textual/visual). Mention if values are outside typical reference ranges if that information is available or commonly known (state typical ranges if possible).
        2.  **Explain Significance:** For key abnormal findings, explain what they *might* indicate in simple terms.
        3.  **Potential Conditions (General):** Based on the *combination* of findings, list *potential* conditions or areas of concern that *might* be associated with these results. Use cautious language (e.g., "could suggest," "may indicate," "warrants further investigation").
        4.  **General Recommendations & Next Steps:** Suggest general, non-specific lifestyle advice (like diet, hydration, exercise) that might be relevant *if applicable and safe*. More importantly, strongly recommend discussing these results in detail with a qualified healthcare professional for accurate diagnosis and treatment planning. Mention specific results they should discuss.

        **IMPORTANT:**
        * **DO NOT PROVIDE A DIAGNOSIS.** You are not a doctor.
        * **DO NOT PROVIDE MEDICAL ADVICE.** All recommendations must be general and emphasize consultation with a doctor.
        * Clearly state that this analysis is based solely on the provided data and may be incomplete or require clinical context.
        * If the report seems incomplete or unclear, state that.

        Use the following extracted information and images (if any) for your analysis.

        **Extracted Text Summary/Details:**
        [PLACEHOLDER_FOR_INITIAL_ANALYSIS_OR_FULL_TEXT]

        **[If Images Exist]:** Analyze the provided images in conjunction with the text. Describe any visual findings.
        """

        # --- Execute Analysis ---
        analysis_result = {}

        try:
            # Step 1: Initial extraction and text analysis (using text model)
            st.write("Step 1: Extracting structured data from text...")
            initial_analysis = call_gemini_text(extraction_prompt)
            if not initial_analysis:
                st.warning("Could not perform initial text analysis.")
                # Fallback: use raw text if initial analysis fails
                initial_analysis = "Could not pre-process text. Using raw text for synthesis."
                text_for_synthesis = full_text
            else:
                 st.write("Initial Text Analysis Complete.")
                 analysis_result['initial_extraction'] = initial_analysis
                 text_for_synthesis = initial_analysis # Use the structured summary for the next step


            # Step 2: Synthesize results (using Vision model if images exist)
            st.write("Step 2: Performing overall synthesis and interpretation...")
            final_prompt = synthesis_prompt.replace("[PLACEHOLDER_FOR_INITIAL_ANALYSIS_OR_FULL_TEXT]", text_for_synthesis)

            if image_bytes_list:
                st.info(f"Analyzing text along with {len(image_bytes_list)} image(s)...")
                final_analysis = call_gemini_vision(final_prompt, image_bytes_list)
            else:
                st.info("Analyzing text data only (no images found/processed)...")
                final_analysis = call_gemini_text(final_prompt) # Use text model if no images

            if not final_analysis:
                 st.error("Failed to generate the final analysis.")
                 return None
            else:
                st.write("Final Analysis Complete.")
                analysis_result['final_analysis'] = final_analysis

        except Exception as e:
            st.error(f"An error occurred during analysis: {e}")
            return None

        return analysis_result