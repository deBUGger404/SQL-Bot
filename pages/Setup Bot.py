import os
import streamlit as st
from module.ui_module import setup_bot_sidebar, setup_page
from module.utils import get_openai_config, init_season, load_env

# setup page icon and name
setup_page()

# setup side bar
setup_bot_sidebar()

def save_uploaded_file(uploaded_file):
    try:
        with open(os.path.join(".", uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
        return True
    except Exception as e:
        # Handle exceptions
        return False

print('here is the code:' , st.session_state)
# Check if the file has been uploaded
if 'uploaded_env_file' not in st.session_state or st.session_state.uploaded_env_file is None:
    # File uploader
    uploaded_file = st.file_uploader("Upload an .env file", type=['env'])
    if uploaded_file is not None:
        # Save the uploaded file
        if save_uploaded_file(uploaded_file):
            st.success(f"File '{uploaded_file.name}' uploaded successfully!")
            st.session_state.uploaded_env_file = uploaded_file.name
            load_env()
            config = get_openai_config()
            init_season(config)
            # You can disable the manual input form here by not rendering it
        else:
            st.error("Failed to upload the file.")
    else:
        # Manual input form (rendered only if no file has been uploaded)
        with st.form("env_form"):
            api_key = st.text_input("API Key")
            api_base = st.text_input("API Base")
            # Add other fields as needed

            submitted = st.form_submit_button("Submit")
            if submitted:
                # Process the manually entered data
                st.session_state.api_key = api_key  # Store in session state or handle as needed
                # Handle other fields similarly
else:
    st.info(f"Uploaded .env file: {st.session_state.uploaded_env_file}")
    st.write("The manual entry is disabled since an .env file has been uploaded.")
    # You might want to allow users to remove the uploaded file and re-enable the form
    if st.button("Remove uploaded .env file"):
        del st.session_state.uploaded_env_file  # Remove the uploaded file info from session state
        # You could also delete the file from the server if needed
