from contextlib import contextmanager
import os
from pathlib import Path
from uuid import uuid4
import streamlit as st
import sqlite3
import pandas as pd
from sqlalchemy import create_engine

from module.ui_module import connect_db_sidebar, setup_page
from module.utils import get_openai_config, init_season

# setup side bar
setup_page()

# setup side bar
connect_db_sidebar()

# Attempt to initialize and catch any errors
try:
    # Attempt to retrieve the OpenAI configuration and initialize the season
    config = get_openai_config()
    init_season(config)  # Assuming init_season now takes config as a parameter
except ValueError as e:
    st.warning(f"Please upload database and Setup OpenAI credentials: {e}")
    st.stop()  # Prevent further execution

# Function to establish a connection to a SQLite database
@contextmanager
def sqlite_connect(file_path):
    conn = sqlite3.connect(file_path)
    try:
        yield conn
    finally:
        conn.close()

# Function to convert and save a file to SQLite database format
def convert_and_save_file(uploaded_file, file_type):
    db_file_path = f"./uploaded_data/{str(uuid4())}.db"
    if not os.path.exists('./uploaded_data'):
        os.makedirs('./uploaded_data')
    
    if file_type in ["db", "sqlite"]:
        with open(db_file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
    else:
        if file_type == "xlsx":
            df = pd.read_excel(uploaded_file)
        elif file_type == "parquet":
            df = pd.read_parquet(uploaded_file)
        
        engine = create_engine(f'sqlite:///{db_file_path}')
        df.to_sql(name="uploaded_data", con=engine, index=False, if_exists="replace")

    st.session_state.db_file_path = db_file_path
    st.session_state.uploaded_data_file = uploaded_file.name  # Track the uploaded file name

def display_data_from_db():
    db_file_path = st.session_state.get("db_file_path")
    if db_file_path:
        with sqlite_connect(db_file_path) as conn:
            # Fetch the list of all tables in the database
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()  # This returns a list of tuples

            if tables:
                # Extract table names from tuples
                table_names = [table[0] for table in tables]
                
                # Let the user select a table to view
                selected_table = st.selectbox('Select a table to display', table_names)
                
                # Display the selected table
                query = f"SELECT * FROM {selected_table}"
                df = pd.read_sql_query(query, conn)
                st.dataframe(df)
            else:
                st.error("The database does not contain any tables.")
    else:
        st.error("No database file found. Please upload a file first.")

# File uploader logic
if 'uploaded_data_file' not in st.session_state or st.session_state.uploaded_data_file is None:
    uploaded_file = st.file_uploader("Upload a file", type=['db', 'sqlite', 'parquet', 'xlsx'])
    if uploaded_file is not None:
        file_type = uploaded_file.name.split('.')[-1].lower()
        with st.spinner("Converting and saving file..."):
            convert_and_save_file(uploaded_file, file_type)
        st.success("File uploaded and converted successfully!")
        display_data_from_db()
    else:
        st.stop()
else:
    st.info(f"Uploaded file: {st.session_state['uploaded_data_file']}")
    file_type = st.session_state['uploaded_data_file'].split('.')[-1].lower()
    if file_type in ['xlsx', 'db', 'sqlite', 'parquet']:
        st.markdown(f"**File Type:** {file_type.upper()}")
        if file_type != 'db' and file_type != 'sqlite':
            display_data_from_db()
    else:
        st.warning("Unsupported file type. Please upload a valid file.")
    
    if st.button("Remove uploaded file"):
        if os.path.exists(st.session_state['db_file_path']):
            os.remove(st.session_state['db_file_path'])
        del st.session_state['db_file_path']
        del st.session_state['uploaded_data_file']
        st.success("Uploaded file removed successfully.")