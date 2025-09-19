import os
import sys
import tempfile

import streamlit as st

# Set page configuration for full width
st.set_page_config(
    layout="wide",  # Use wide layout
    page_title="📚 BibTeX Processing Tool",
    initial_sidebar_state="collapsed",  # Hide sidebar for more space
)

# Add custom CSS for full width and better styling
st.markdown(
    """
<style>
    .main .block-container {
        max-width: 100% !important;
        padding-left: 5rem;
        padding-right: 5rem;
        padding-top: 2rem;
    }

    .stTextArea textarea {
        font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
        font-size: 14px;
        line-height: 1.4;
    }

    .stButton button {
        width: 100%;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    .stUploader {
        margin-bottom: 1rem;
    }

    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
        margin-bottom: 1rem;
    }

    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
        margin-bottom: 1rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Add the parent directory to Python path to enable imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from pybibtexer.tools.format_save_bibs import format_bib_to_abbr_or_zotero_or_save_mode
except ImportError:
    st.error("Could not import required modules. Please check your installation.")
    st.stop()

# Set page title with centered alignment
st.markdown(
    "<h1 style='text-align: center; margin-bottom: 2rem;'>📚 BibTeX Processing Tool</h1>", unsafe_allow_html=True
)

# Create two columns with 8:2 ratio and some spacing
left_col, right_col = st.columns([7, 3], gap="large")

with left_col:
    # Input section
    st.markdown("### 📥 Input BibTeX Data")
    bibtex_input = st.text_area(
        "Paste your BibTeX data here:",
        height=300,
        placeholder="""@article{key,
  author = {Author Name},
  title = {Paper Title},
  journal = {Journal Name},
  year = {2025}
}""",
        help="Copy and paste your BibTeX entries directly into this text area",
        label_visibility="collapsed",
    )

    # Output section
    if "processed_result" in st.session_state and st.session_state.processed_result:
        st.markdown("### 📤 Processed Result")
        st.text_area(
            "Processed BibTeX output:",
            value=st.session_state.processed_result,
            height=300,
            key="output_area",
            label_visibility="collapsed",
        )

with right_col:
    st.markdown("### ⚙️ Controls")

    # File uploaders with better styling
    with st.container():
        st.markdown("**Additional Files:**")
        uploaded_file_2 = st.file_uploader(
            "Conference Abbreviations File (Optional)", type=["json"], help="Optional additional configuration file"
        )

        uploaded_file_3 = st.file_uploader(
            "Journal Abbreviations File (Optional)", type=["json"], help="Optional additional configuration file"
        )

    # Processing options in a neat container
    with st.container():
        st.markdown("**Processing Options:**")
        col1, col2 = st.columns(2)
        with col1:
            format_options = {
                "abbr": "Abbreviated (short names)",
                "zotero": "Zotero (import optimized)",
                "save": "Save (original data)",
            }

            purpose = st.selectbox(
                "Format Style",
                options=list(format_options.keys()),
                format_func=lambda x: format_options[x],
                help="Select bibliography formatting style",
            )

        with col2:
            maximum_authors_for_abbr = st.selectbox(
                "Max authors before 'et al.'", [1, 2, 3, 10000], help="Authors to show before abbreviation"
            )

        # Abbreviation level options
        if purpose == "abbr":
            st.markdown("**Abbreviation Levels:**")
            col1, col2 = st.columns(2)
            with col1:
                abbr_index_article_for_abbr = st.selectbox(
                    "Articles", options=[0, 1, 2], index=1, help="Article abbreviation level"
                )
            with col2:
                abbr_index_inproceedings_for_abbr = st.selectbox(
                    "Inproceedings", options=[0, 1, 2], index=2, help="Inproceedings abbreviation level"
                )
        else:
            abbr_index_article_for_abbr = 1
            abbr_index_inproceedings_for_abbr = 2

    # Process button with prominent styling
    process_btn = st.button(
        "🔄 Process BibTeX",
        type="primary",
        use_container_width=True,
        help="Process the BibTeX data with selected options",
    )

    # Download button (only show when there's a result)
    if "processed_result" in st.session_state and st.session_state.processed_result:
        st.download_button(
            label="📥 Download Result",
            data=st.session_state.processed_result,
            file_name="processed_bibtex.bib",
            mime="text/plain",
            use_container_width=True,
            help="Download the processed BibTeX file",
        )

# Processing logic
if process_btn:
    if not bibtex_input.strip():
        st.error("Please paste some BibTeX data first!")
    else:
        try:
            # Save input to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".bib", mode="w", encoding="utf-8") as tmp:
                tmp.write(bibtex_input)
                tmp_path = tmp.name

            # Save additional files if provided
            tmp_path_2 = None
            tmp_path_3 = None

            if uploaded_file_2:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp2:
                    tmp2.write(uploaded_file_2.getvalue())
                    tmp_path_2 = tmp2.name

            if uploaded_file_3:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp3:
                    tmp3.write(uploaded_file_3.getvalue())
                    tmp_path_3 = tmp3.name

            # Process the data
            options = {
                "choose_abbr_zotero_save": purpose,
                "maximum_authors_for_abbr": maximum_authors_for_abbr,
                "abbr_index_article_for_abbr": abbr_index_article_for_abbr,
                "abbr_index_inproceedings_for_abbr": abbr_index_inproceedings_for_abbr,
            }

            with st.spinner("Processing BibTeX data..."):
                abbr, zotero, save = format_bib_to_abbr_or_zotero_or_save_mode(
                    tmp_path, options, tmp_path_2 if tmp_path_2 else "", tmp_path_3 if tmp_path_3 else ""
                )

            # Determine result based on selected format
            if purpose == "abbr":
                result = "".join(abbr)
            elif purpose == "zotero":
                result = "".join(zotero)
            elif purpose == "save":
                result = "".join(save)
            else:
                result = ""

            # Store result in session state
            st.session_state.processed_result = result
            st.success("✅ Processing completed successfully!")

            # Clean up temporary files
            try:
                os.unlink(tmp_path)
                if tmp_path_2:
                    os.unlink(tmp_path_2)
                if tmp_path_3:
                    os.unlink(tmp_path_3)
            except Exception as e:
                st.warning(f"Note: Temporary files cleanup failed: {e}")

        except Exception as e:
            st.error(f"❌ Processing error: {e}")
            st.exception(e)

# Instructions in an expander
with st.expander("ℹ️ How to use", expanded=False):
    st.markdown(
        """
    ### Usage Instructions:

    1. **Paste** your BibTeX data into the left text area
    2. **Upload** any additional files (optional)
    3. **Select** your desired format and options
    4. **Click** the Process button
    5. **View** the processed result in the left panel
    6. **Download** the result using the download button

    ### Format Options:
    - **Abbreviated**: Shortened journal and booktitle names
    - **Zotero**: Optimized for Zotero reference manager import
    - **Save**: Preserves all original data without changes
    """
    )

# Initialize session state if not exists
if "processed_result" not in st.session_state:
    st.session_state.processed_result = ""
