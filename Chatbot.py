# __import__('pysqlite3')
# import sys
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import re
import streamlit as st
from module.ui_module import chatbot_sidebar, setup_page
from module.utils import *
from dotenv import load_dotenv


# setup page icon and name
setup_page()
# setup side bar
chatbot_sidebar()

print('chatbot session',st.session_state)
# Attempt to initialize and catch any errors
try:
    # Attempt to retrieve the OpenAI configuration and initialize the season
    config = get_openai_config()
    init_season(config)  # Assuming init_season now takes config as a parameter
except ValueError as e:
    st.warning(f"Please upload database and Setup OpenAI credentials: {e}")
    st.stop()  # Prevent further execution

print('Current DB Name:')
st.write(f"Current DB Name: {st.session_state.db_name}")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "InsightGenix: Your expert guide through the relational database maze. How can I assist you today with your database queries?"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if 'results' in message.keys():
            st.dataframe(message["results"], use_container_width=True)

# Call init_season() with the appropriate configuration dict
client = azure_openai(config=config)
data = st.session_state.db


if prompt := st.chat_input(placeholder="Provide the data where biomarker is her2 positive?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if not st.session_state.openai_key or not st.session_state.chat_model_name:
        st.info("Please correctly provide your OpenAI API key and deployment model name to continue.")
        st.stop()

    if prompt.startswith('query:'):
        middle_prompt = get_relevent_prompt(prompt, data)
        print(middle_prompt)
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model= config['chat_model_name'],
                messages=middle_prompt,
                stream=True,
            )
            response = st.write_stream(stream)
        message = {"role": "assistant", "content": response}
        print(type(response), response)
        sql_match = re.search(r"```sql\n(.*)\n```", response, re.DOTALL)
        with st.spinner('Getting insights from database based on the query.....'):
            if sql_match:
                sql = sql_match.group(1)
                print('path of databse', st.session_state.db_file_path)
                try:
                    results = query_to_dataframe(st.session_state.db_file_path, sql)
                    # Convert DataFrame to a string with pipe-separated values
                    result_str = results.head(1).to_csv(sep='|', index=False, lineterminator='\n')
                    message["results"] = results
                    message["result_str"] = result_str
                    st.dataframe(message["results"], use_container_width=True)
                except Exception as e:
                    message["results"] = ''
                    message["result_str"] = ''
                    st.error(f"An error occurred: {e}")

    elif prompt.startswith('insight:'):
        with st.chat_message("assistant"):
            try:
                my_list = st.session_state.messages
                idx = -(next(i for i, d in enumerate(my_list[::-1]) if 'result_str' in d) + 2)
                print("Latest dict with result:", my_list[idx + 1])
                print("Dict just above the latest with result:", my_list[idx])
                stream = client.chat.completions.create(
                    model= config['chat_model_name'],
                    messages=[
                        {"role": "system", "content": main_sys_prompt()},
                        {"role": "user", "content": prompt + f"\n#### Inquiry\n**Question:** {my_list[idx]['content']}\n\n#### Data Overview\n**Query Result:**  {my_list[idx + 1]['result_str']}"},
                    ],
                    stream=True,
                )
                response = st.write_stream(stream)
            except StopIteration:
                response = "I'm sorry, but without knowing specifically which data you are referring to, I am unable to provide a description. Could you please ask the question again?"
            message = {"role": "assistant", "content": response}
    else:
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model= config['chat_model_name'],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )
            response = st.write_stream(stream)
            message = {"role": "assistant", "content": response}
    st.session_state.messages.append(message)
    print('hi bro', st.session_state.messages, '\n')