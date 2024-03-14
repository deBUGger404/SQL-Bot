import os
import shutil
import sqlite3
from typing import Tuple
import uuid
import pandas as pd
from dotenv import load_dotenv
import streamlit as st
from openai import AzureOpenAI
from chroma_db.chroma_vector import ChromaDB_VectorStore

def load_env():
    if 'uploaded_env_file' in st.session_state:
        print('uploaded_env_file:', st.session_state.uploaded_env_file)
        load_dotenv(st.session_state.uploaded_env_file)
    else:
        st.warning('API key is required but not provided.')


def get_openai_config() -> dict:
    api_key = os.environ.get("OPENAI_API_KEY")
    api_base = os.environ.get("OPENAI_API_BASE")
    api_type = os.environ.get("OPENAI_API_TYPE")
    api_version = os.environ.get("OPENAI_API_VERSION")
    embedding_model_name = os.environ.get("EMBEDDING_MODEL_NAME")
    chat_model_name = os.environ.get("CHAT_MODEL_NAME")

    config = {
        "api_key": api_key,
        "api_base": api_base,
        "api_type": api_type,
        "api_version": api_version,
        "chat_model_name": chat_model_name,
        "embedding_model_name": embedding_model_name
    }
    return config
    
def find_latest_folder(db_path: str):
    # Check if the data folder exists
    if not os.path.exists(db_path):
        print("The specified path does not exist.")
        return None

    # Get the list of directories in the db_path
    directories = [d for d in os.listdir(db_path) if os.path.isdir(os.path.join(db_path, d))]
    print('Directories:', directories)

    if not directories:
        print("No directories found in the specified path.")
        return None

    # Sort directories by their modification time in descending order
    latest_directory = max(directories, key=lambda x: os.path.getmtime(os.path.join(db_path, x)))

    print(f"Latest directory: {latest_directory}")
    return latest_directory

def init_chromadb(config: dict, db_path: str = './data/db_data/') -> Tuple:
    """
    Initialize a new ChromaDB instance or return the existing instance.

    Parameters:
        config (dict): Configuration dictionary containing OpenAI settings.
        db_path (str): Path to the database directory.

    Returns:
        Tuple: A tuple containing the ChromaDB instance and the database name.
    """
    # Check if the data folder exists and create it if not
    os.makedirs(db_path, exist_ok=True)
    latest_folder = find_latest_folder(db_path)
    print('latest_folder',latest_folder)
    # Check if the folder is empty
    if latest_folder:
        # If not empty, read from the latest file
        db_path = os.path.join(db_path, latest_folder)
        print(f"Reading from existing database: {latest_folder}")
    else:
        # If empty, create a new database file
        new_db_name = 'chroma_database_' + str(uuid.uuid4())
        db_path = os.path.join(db_path, new_db_name)
        # Ensure the new database directory exists
        os.makedirs(db_path, exist_ok=True)
        print(f"Creating new database: {new_db_name}")

    # Initialize a new ChromaDB instance with the provided configuration
    db = ChromaDB_VectorStore(config={'path': db_path, **config})
    return db, os.path.basename(db_path)


def reset_chromadb(db_path: str = './data/db_data/') -> None:
    """
    Deletes the existing database,

    Parameters:
        config (dict): Configuration dictionary.
        db_path (str): Base path for the database directories.
    """
    # Delete existing database directory if it exists in session state
    if 'db_name' in st.session_state:
        existing_db_path = os.path.join(db_path, st.session_state.db_name)
        if os.path.exists(existing_db_path):
            shutil.rmtree(existing_db_path)
            print(f"Deleted existing database: {st.session_state.db_name}")
            # Also remove the db and db_name from session state
            del st.session_state['db_name']
            if 'db' in st.session_state:
                del st.session_state['db']

def init_season(config: dict):
    # Initialize and store the DB in session state if it's not already done
    
    if 'db' not in st.session_state or 'db_name' not in st.session_state:
        print('here i am ')
        st.session_state.db, st.session_state.db_name = init_chromadb(config=config)
        st.session_state.openai_key = config['api_key']
        st.session_state.chat_model_name = config['chat_model_name']
        print(f'Database setup done: {st.session_state.db_name}')
    
def query_to_dataframe(db_file: str, query: str) -> pd.DataFrame:
    """
    Retrieve data from an SQLite database file and convert it into a DataFrame.

    Parameters:
        db_file (str): Path to the SQLite database file.
        query (str): SQL query to execute.

    Returns:
        pd.DataFrame: DataFrame containing the fetched data.
    """

    # Connect to SQLite database
    conn = sqlite3.connect(db_file)
    
    # Create a cursor object
    cursor = conn.cursor()
    
    # Execute SQL query and fetch the results
    cursor.execute(query)
    data = cursor.fetchall()
    
    # Get column names from cursor description
    columns = [description[0] for description in cursor.description]
    
    # Create DataFrame from fetched data and column names
    df = pd.DataFrame(data, columns=columns)
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
    return df

def azure_openai(config: dict):
    
    client = AzureOpenAI(
        api_key= config['api_key'],  
        api_version= config['api_version'],
        azure_endpoint = config['api_base']
        )
    return client

def str_to_approx_token_count(string: str) -> int:
        return len(string) / 4

def add_ddl_to_prompt(
         ddl_list: list[str], max_tokens: int = 14000
    ) -> str:
        initial_prompt = ''
        if len(ddl_list) > 0:

            for ddl in ddl_list:
                if (
                    str_to_approx_token_count(initial_prompt)
                    + str_to_approx_token_count(ddl)
                    < max_tokens
                ):
                    initial_prompt += f"{ddl}\n\n"

        return initial_prompt

# static_documentation = "This is a SQLite database"

def add_documentation_to_prompt(
        documentation_list: list[str],
        max_tokens: int = 14000,
    ) -> str:
        initial_prompt = ''
        if len(documentation_list) > 0:

            for documentation in documentation_list:
                if (
                    str_to_approx_token_count(initial_prompt)
                    + str_to_approx_token_count(documentation)
                    < max_tokens
                ):
                    initial_prompt += f"{documentation}\n\n"

        return initial_prompt

def system_message( message: str) -> any:
        return {"role": "system", "content": message}

def user_message(message: str) -> any:
    return {"role": "user", "content": message}

def assistant_message(message: str) -> any:
    return {"role": "assistant", "content": message}
def get_sql_prompt(
        question: str,
        question_sql_list: list,
        ddl_list: list,
        doc_list: list,
        **kwargs,
    ):
        """
        Example:
        ```python
        vn.get_sql_prompt(
            question="What are the top 10 customers by sales?",
            question_sql_list=[{"question": "What are the top 10 customers by sales?", "sql": "SELECT * FROM customers ORDER BY sales DESC LIMIT 10"}],
            ddl_list=["CREATE TABLE customers (id INT, name TEXT, sales DECIMAL)"],
            doc_list=["The customers table contains information about customers and their sales."],
        )

        ```

        This method is used to generate a prompt for the LLM to generate SQL.

        Args:
            question (str): The question to generate SQL for.
            question_sql_list (list): A list of questions and their corresponding SQL statements.
            ddl_list (list): A list of DDL statements.
            doc_list (list): A list of documentation.

        Returns:
            any: The prompt for the LLM to generate SQL.
        """
        initial_prompt = """
As an SQL Expert named QueryGenix., your primary task is to generate Always SELECT SQL queries in response to user questions.
Your goal is to give correct, executable sql query to users.
Your responses should exclusively consist of SQL code, without any explanatory text. 
You are given one table, the table name/column names are in DDL and documentation of table and columns is on Documentation
Use insights from past queries to guide your current responses.

**DDL:** {ddl}

**Documentation:** <documentation>{document}</documentation>

Here are 6 critical rules for the interaction you must abide:
<rules>
1. You MUST MUST wrap the generated sql code within ``` sql code markdown in this format e.g
```sql
(select 1) union (select 2)
```
- Unless specifically instructed to retrieve all results, **ALWAYS** limit your query outcomes to a maximum of 10 records.
- For string/text searches, Always, adhere to the following practices,
   - Perform case-insensitive comparisons by using the `LOWER()` function to ensure uniformity in string comparison (e.g., LOWER(name) like %her2%).
   - Utilize the LIKE operator with wildcard characters (%) for partial matches, enabling fuzzy searching within text fields. This is particularly useful when an exact match for the input term might not exist in the database/documentation.
- Construct a single, comprehensive SQL query per user request.
- Strictly use table names and columns as outlined in the provided DDL statements. Do not introduce or assume the existence of tables or columns not specified in these statements.
- Analyze the context within user queries and the documentation provided to craft precise SQL code. Modify condition values and the query's logic based on the **DDL/DOCUMENTATION** to ensure the generated SQL accurately captures the required data.
- Always select only the relevant columns specified by the user to optimize performance and data relevance. Avoid using `SELECT *` unless explicitly instructed. Adjust the column selection based on the user's requirements.
- Generate Always SELECT statements for data retrieval; refrain from creating any DML statements (INSERT, UPDATE, DELETE, DROP, etc.). If a user requests a DML statement query, respond with 'This operation is prohibited by the admin. Please contact them for further assistance.' Violation of this guideline may result in penalties as stated.
- INCUR A PENALTY OF $1000 FOR FAILING TO PROVIDE CORRECT SQL QUERIES,  INCLUDING VIOLATING THE DML STATEMENT PROHIBITION.
- EARN A REWARD OF $1000 FOR CORRECTLY UTILIZING THE PROVIDED INFORMATION TO SUPPLY ACCURATE SQL QUERIES.
- Stricly, Follow the SQL clause formatting as demonstrated in the examples: ```sql\n<sql code>\n```
</rules>

## Correct/Wrong Output Example:
Question: Provide the all data where drug name is Sotorasib.

Wrong Output: 
Of course, here is your query,
```sql SELECT drug_name, drug_class, therapeutic_area, expected_launch_date 
FROM hy_table
WHERE lower(drug_name) like '%sotorasib%'
AND Estimated ttm_expected_date_in_us < '2024-07-01'
LIMIT 10;
```
resaon: OperationalError: no such column: drug_class, therapeutic_area, expected_launch_date

Correct Output: 
Of course, here is your query,
```sql
SELECT drug_name, disease_name, drug_disease_status, drug_delivery_route, moa, target_name 
FROM hy_table
WHERE lower(drug_name) like '%sotorasib%'
AND ttm_expected_date_in_us < '2024-07-01'
LIMIT 10;
```
"""
        ddl_prompt = add_ddl_to_prompt(
            ddl_list, max_tokens=14000
        )

        # if static_documentation != "":
        #     doc_list.append(static_documentation)

        doc_prompt = add_documentation_to_prompt(
            doc_list, max_tokens=14000
        )

        initial_prompt1 = initial_prompt.format(ddl=ddl_prompt, document=doc_prompt)    

        message_log = [system_message(initial_prompt1)]

        for example in question_sql_list:
            if example is None:
                print("example is None")
            else:
                if example is not None and "question" in example and "sql" in example:
                    message_log.append(user_message(example["question"]))
                    message_log.append(assistant_message(example["sql"]))

        message_log.append(user_message(question))

        return message_log

def get_relevent_prompt(question: str, db):
    # question = "update me about the top 100 data where Modality should be Peptide"
    question_sql_list = db.get_similar_question_sql(question)
    ddl_list = db.get_related_ddl(question)
    doc_list = db.get_related_documentation(question)
    prompt = get_sql_prompt(
            question=question,
            question_sql_list=question_sql_list,
            ddl_list=ddl_list,
            doc_list=doc_list,
        )
    return prompt

def main_sys_prompt():
     return """### Data Analysis Insight Brief

#### Context
As an expert in data analysis, your task is to examine the provided dataset and extract key insights, patterns, and potential challenges. Your analysis should focus on providing actionable recommendations based on the findings.

**Output Format:**
#### Summary
Provide a concise summary of the critical insights derived from the dataset, emphasizing their significance and implications.

#### Top 10 Results
(Include this section only if applicable. List the top 10 based on relevance or importance. If fewer than 10 entries, adjust accordingly.)

| Rank | Item | Category | Metric 1 | Metric 2 | Metric 3 |
|------|------|----------|----------|----------|----------|
| ...  | ...  | ...      | ...      | ...      | ...      |

#### Detailed Analysis
Offer a thorough analysis of the dataset, delving into the implications of the findings and their potential impact on decision-making processes.

### Additional Insights (If Requested)
If further insights are desired, address the following areas:

- **Trends:** Identify emerging trends or patterns within the dataset, such as shifts over time or correlations between variables.
  
- **Challenges:** Discuss any challenges or limitations encountered during the analysis, including data quality issues or methodological constraints.
  
- **Recommendations:** Propose actionable recommendations based on the analysis, suggesting potential strategies for improvement or future research directions.

### Conclusion
Conclude by synthesizing the insights gathered from the analysis and outlining potential next steps or considerations for stakeholders.
"""