from PIL import Image
import streamlit as st

# Define a function to set up the Streamlit page configuration
# @st.cache_data
def setup_page():
    PAGE_TITLE = "InsightGenix"
    im = Image.open("./components/sql.ico")
    # Initialize the Streamlit page with wide layout
    st.set_page_config(page_title=PAGE_TITLE,
                        page_icon=im, 
                        layout="wide",
                    menu_items={
                    "Get help": "https://github.com/AdieLaine/Streamly",
                    "Report a bug": "https://github.com/AdieLaine/Streamly",
                    "About": f"""
                        ## {PAGE_TITLE} SQL Assistant
                        
                        **GitHub**: (https://github.com/deBUGger404)
                        
                        The AI Assistant named, {PAGE_TITLE}, aims to provide the SQL queries from user query,
                        generate SQL codes,
                        and provide insights about dataset, issues, and more.
                        Streamly has been trained on the latest Streamlit updates and documentation.
                    """
                })

def chatbot_sidebar():
    # Display sidebar for user inputs
    with st.sidebar:
        st.markdown("# Overview")
        st.markdown(
            "Discover insights from your documents with QueryGenix, "
            "your go-to for precise answers and instant source citations."
        )
        st.markdown(
            "As a project in continuous evolution, we welcome your insights "
            "and suggestions. Engage with us on GitHub to shape its future."
        )
        st.markdown("Crafted with care by deBUGger404,")
        "[![Open in GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://github.com/deBUGger404)"

def setup_bot_sidebar():
    with st.sidebar:
        st.title('Setup LLM Keys')
        st.markdown("Upload .env file which contains the openai/Azure Openai Key")

def connect_db_sidebar():
    # Sidebar content
    with st.sidebar:
        st.title('App Information')
        st.markdown("<style>.stMarkdown ul { line-height: 1.3;  margin-bottom: 0; }</style>", unsafe_allow_html=True)
        st.markdown("""
        Welcome to the Data Query App! Upload a file to get started.
        
        ### Supported File Types:
        - XLSX (Excel files)
        - SQLite databases (.db, .sqlite)
        - Parquet files (.parquet)
        
        ### Instructions:
        1. Upload a file using the file uploader.
        2. Supported file types are XLSX, SQLite databases, and Parquet files.
        3. After uploading, the app will display relevant information based on the file type.
        4. You can remove the uploaded file if needed.
        """)

def trainllm_sidebar():
    with st.sidebar:
        st.title("Train LLM")
        # Applying custom CSS to adjust the margin of unordered lists in markdown
        st.markdown("<style>.stMarkdown ul { line-height: 1.3;  margin-bottom: 0; }</style>", unsafe_allow_html=True)

        # Introduction to the training section
        st.markdown("""
    Train your LLM on your relational database using the following parameters:

    - **DDL (Data Definition Language)**
    - Table Name: Enter the name of the table you want to extract DDL statements from.
    - DDL Statement Input: Provide the DDL statements corresponding to the table.

    - **Questions and SQL Queries**
    - Questions: Input the questions you want the LLM to be trained on.
    - SQL Queries: Enter the SQL queries corresponding to the questions provided.

    - **Documentation**
    - Documentation: Please add documentation that clarifies the terms or definitions used in your business, such as column definitions or unique column values.
    """, unsafe_allow_html=True)