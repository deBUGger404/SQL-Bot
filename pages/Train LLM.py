import uuid
from PIL import Image
import streamlit as st
from module.ui_module import setup_page, trainllm_sidebar
from module.utils import *

# setup side bar
setup_page()

# setup side bar
trainllm_sidebar()

# Attempt to initialize and catch any errors
try:
    # Attempt to retrieve the OpenAI configuration and initialize the season
    config = get_openai_config()
    init_season(config)  # Assuming init_season now takes config as a parameter
except ValueError as e:
    st.warning(f"Please upload database and Setup OpenAI credentials: {e}")
    st.stop()  # Prevent further execution

def send_data_to_function(type: str, data: list):
    # Placeholder function to simulate sending data
    # Replace this with actual functionality as needed
    with st.spinner('Processing...'):
        if type == 'ddl':
            for i in data:
                st.session_state.db.train(ddl=i)
        elif type == 'Question/Query':
            for i in data:
                st.session_state.db.train(sql=i)
        elif type == 'Documentation':
            for i in data:
                st.session_state.db.train(documentation=i)
        else:
            st.warning('select correct training type.')
    st.success(f'{type} training data added successfully!')


def train_model_1():
    st.subheader("DDL Parameters")
    
    # Parameter 1: Table Name
    table_name = st.text_input("Table Name", 
                               "",
                               placeholder='Provide Table Name ...')
    
    # Parameter 2: DDL Statement (big text box)
    ddl_statement = st.text_area("DDL Statement", "", height=300,
                                 placeholder="""CREATE TABLE IF NOT EXISTS my-table (
        id INT PRIMARY KEY,
        name VARCHAR(100),
        age INT
    )""")
    
    if st.button("Train DDL Model"):
        # Generate a unique identifier
        unique_id = str(uuid.uuid4())
        
        # Create JSON object
        data_json = [
            {
                'id': unique_id,
                'table_name': table_name,
                'ddl_statement': ddl_statement
            }
        ]
        
        # Call the placeholder function with the JSON data
        send_data_to_function(type='ddl', data=data_json)
        
        # Feedback to user
        st.write("Training DDL model started with the following data:")
        st.json(data_json[0])  # This will nicely format the JSON in the UI

def train_model_2():
    st.subheader("Question-SQL Parameters")
    
    # Input box for the Question
    question = st.text_input("Question", "",
                             placeholder="Provide name and age of person where name is John Doe")
    
    # Text area for the Query
    query = st.text_input("SQL Query", "",
                          placeholder="SELECT name, age FROM my-table WHERE name = 'John Doe'")
    
    if st.button("Train QS Model"):
        # Generate a unique identifier
        unique_id = str(uuid.uuid4())
        
        # Create JSON object
        data_json = [
            {
                'id': unique_id,
                'question': question,
                'query': query
            }
        ]
        
        # Call the function with the JSON data
        send_data_to_function(type='Question/Query', data=data_json)

        # Feedback to user
        st.write("Training DDL model started with the following data:")
        st.json(data_json[0])  # This will nicely format the JSON in the UI

def train_model_3():
    st.subheader("Documentation Parameters")
    
    # Big text area for the Documentation
    documentation = st.text_area("Documentation", "", 
                                 height=300,
                                 placeholder="`Name`: Column contains person's name.\n`Age`: Column contains person's age.\n Name column unique value: Ramesh, John, Ravi")
    
    if st.button("Train Documentation Model"):
        # Generate a unique identifier
        documentation_list = documentation.split('\n')
        data_json_list = []
        for index, doc in enumerate(documentation_list):
            unique_id = str(uuid.uuid4())
            json_object = {
                'id': unique_id, 
                'documentation': doc
            }
            # Append the JSON object to the list
            data_json_list.append(json_object)
        
        # Call the function with the JSON data
        send_data_to_function(type='Documentation', data=data_json_list)

        # Feedback to user
        st.write("Training DDL model started with the following data:")
        st.json(data_json_list)  # This will nicely format the JSON in the UI

def train_model_4():
    st.subheader("Training DataBase")
    show = False  # Initialize 'show' flag
    db_message = None  # Initialize message variable
    rm_message = None
    
    # Layout for buttons: Show Database, Delete and Create New Database
    col1, col2 = st.columns(2)
    with col1:
        if st.button('Show Database'):
            df = st.session_state.db.get_training_data()
            show = True

    with col2:
        if st.button('Delete Database'):
            data = st.session_state.db_name
            reset_chromadb()
            rm_message = f"database Delete: {data}"
            init_season()
            db_message = f"New database created: {st.session_state.db_name}"
            show = False
    # Display success message outside columns if db_message is set
    if rm_message:
        st.success(rm_message)
    if db_message:
        st.success(db_message)
        
    if show:
        # Display the DataFrame
        st.dataframe(df, use_container_width=True)

# st.write(f'from page 1, value of ss with key "a" is {st.session_state.db}')
# Step 1: Tabs
tab1, tab2, tab3, tab4 = st.tabs(["DDL Statements", "Question-SQL Query", "Data Documentions", "Display Training Data"])

with tab1:
    train_model_1()
with tab2:
    train_model_2()
with tab3:
    train_model_3()
with tab4:
    train_model_4()
