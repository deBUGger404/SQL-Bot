import json
import uuid
from typing import List

import chromadb
import pandas as pd
from chromadb.config import Settings
from openai_llm.openai_embedding import OpenAI_Embeddings

class ChromaDB_VectorStore():
    def __init__(self, config=None):
        self.config = config
        self.run_sql_is_set = False
        self.static_documentation = ""
         # Initialize the OpenAI_Embeddings instance
        self.openai_embedfuc = OpenAI_Embeddings(config=self.config)

        # Now, use the chroma_embedding_function to get the setup embedding function
        # This function can be used directly or stored as an attribute for later use
        self.chroma_embedding_func = self.openai_embedfuc.chroma_embedding_function()

        if config is not None:
            path = config.get("path", ".")
            self.embedding_function = config.get("embedding_function", self.chroma_embedding_func)
            curr_client = config.get("client", "persistent")
            self.n_results = config.get("n_results", 10)
        else:
            path = "."
            self.embedding_function = self.chroma_embedding_func
            curr_client = "persistent"  # defaults to persistent storage
            self.n_results = 10  # defaults to 10 documents

        if curr_client == "persistent":
            #print('path',path)
            self.chroma_client = chromadb.PersistentClient(
                path=path, settings=Settings(anonymized_telemetry=False, allow_reset=True)
            )
        elif curr_client == "in-memory":
            self.chroma_client = chromadb.EphemeralClient(
                settings=Settings(anonymized_telemetry=False)
            )
        elif isinstance(curr_client, chromadb.api.client.Client):
            # allow providing client directly
            self.chroma_client = curr_client
        else:
            raise ValueError(f"Unsupported client was set in config: {curr_client}")

        self.documentation_collection = self.chroma_client.get_or_create_collection(
            name="documentation", embedding_function=self.embedding_function, metadata={"hnsw:space": "cosine"}
        )
        self.ddl_collection = self.chroma_client.get_or_create_collection(
            name="ddl", embedding_function=self.embedding_function, metadata={"hnsw:space": "cosine"}
        )
        self.sql_collection = self.chroma_client.get_or_create_collection(
            name="sql", embedding_function=self.embedding_function, metadata={"hnsw:space": "cosine"}
        )

    def generate_embedding(self, data: str, **kwargs) -> List[float]:
        embedding = self.embedding_function([data])
        if len(embedding) == 1:
            return embedding[0]
        return embedding

    def add_question_sql(self, sql: dict, **kwargs) -> str:
        try:
            uid = sql['id']
            question = sql['question']
            sql_query = "Of course, here is your query:\n```sql" + sql['query'] + "```"
        except KeyError as e:
            raise ValueError(f"Missing required key in the 'sql' dictionary: {e}")
        
        question_sql_json = json.dumps(
            {
                "question": question,
                "sql": sql_query,
            },
            ensure_ascii=False,
        )
        id = str(uid) + "-sql"
        self.sql_collection.add(
            documents=question_sql_json,
            embeddings=self.generate_embedding(question_sql_json),
            ids=id,
        )
        # #print('adding sql',
        #     question_sql_json,
        #     self.generate_embedding(question_sql_json),
        #     id,
        # )

        return id

    def add_ddl(self, ddl: dict, **kwargs) -> str:
        try:
            uid = ddl['id']
            # table_name = ddl['table_name']
            ddl_statement = ddl['ddl_statement']
        except KeyError as e:
            raise ValueError(f"Missing required key in the 'sql' dictionary: {e}")
          
        id = str(uid) + "-ddl"
        self.ddl_collection.add(
            documents=ddl_statement,
            embeddings=self.generate_embedding(ddl_statement),
            ids=id,
        )
        # #print('adding ddl',
        #     ddl_statement,
        #     self.generate_embedding(ddl_statement),
        #     id,
        # )
        return id

    def add_documentation(self, docu: dict, **kwargs) -> str:
        try:
            uid = docu['id']
            documentation = docu['documentation']
        except KeyError as e:
            raise ValueError(f"Missing required key in the 'sql' dictionary: {e}")
        id = str(uid) + "-doc"
        self.documentation_collection.add(
            documents=documentation,
            embeddings=self.generate_embedding(documentation),
            ids=id,
        )
        # #print('adding documents',
        #     documentation,
        #     self.generate_embedding(documentation),
        #     id
        # )
        return id

    def get_training_data(self, **kwargs) -> pd.DataFrame:
        sql_data = self.sql_collection.get()
        df = pd.DataFrame()

        if sql_data is not None:
            # Extract the documents and ids
            documents = [json.loads(doc) for doc in sql_data["documents"]]
            ids = sql_data["ids"]

            # Create a DataFrame
            df_sql = pd.DataFrame(
                {
                    "id": ids,
                    "question": [doc["question"] for doc in documents],
                    "content": [doc["sql"] for doc in documents],
                }
            )

            df_sql["training_data_type"] = "sql"
            df = pd.concat([df, df_sql])

        ddl_data = self.ddl_collection.get()
        if ddl_data is not None:
            # Extract the documents and ids
            documents = [doc for doc in ddl_data["documents"]]
            ids = ddl_data["ids"]

            # Create a DataFrame
            df_ddl = pd.DataFrame(
                {
                    "id": ids,
                    "question": [None for doc in documents],
                    "content": [doc for doc in documents],
                }
            )

            df_ddl["training_data_type"] = "ddl"
            df = pd.concat([df, df_ddl])

        doc_data = self.documentation_collection.get()
        if doc_data is not None:
            # Extract the documents and ids
            documents = [doc for doc in doc_data["documents"]]
            ids = doc_data["ids"]

            # Create a DataFrame
            df_doc = pd.DataFrame(
                {
                    "id": ids,
                    "question": [None for doc in documents],
                    "content": [doc for doc in documents],
                }
            )

            df_doc["training_data_type"] = "documentation"
            df = pd.concat([df, df_doc])

        return df

    def remove_training_data(self, id: str, **kwargs) -> bool:
        if id.endswith("-sql"):
            self.sql_collection.delete(ids=id)
            return True
        elif id.endswith("-ddl"):
            self.ddl_collection.delete(ids=id)
            return True
        elif id.endswith("-doc"):
            self.documentation_collection.delete(ids=id)
            return True
        else:
            return False

    def remove_collection(self, collection_name: str) -> bool:
        """
        This function can reset the collection to empty state.

        Args:
            collection_name (str): sql or ddl or documentation

        Returns:
            bool: True if collection is deleted, False otherwise
        """
        if collection_name == "sql":
            self.chroma_client.delete_collection(name="sql")
            self.sql_collection = self.chroma_client.get_or_create_collection(
                name="sql", embedding_function=self.embedding_function
            )
            return True
        elif collection_name == "ddl":
            self.chroma_client.delete_collection(name="ddl")
            self.ddl_collection = self.chroma_client.get_or_create_collection(
                name="ddl", embedding_function=self.embedding_function
            )
            return True
        elif collection_name == "documentation":
            self.chroma_client.delete_collection(name="documentation")
            self.documentation_collection = self.chroma_client.get_or_create_collection(
                name="documentation", embedding_function=self.embedding_function
            )
            return True
        else:
            return False

    @staticmethod
    def _extract_documents(query_results) -> list:
        """
        Static method to extract the documents from the results of a query.

        Args:
            query_results (pd.DataFrame): The dataframe to use.

        Returns:
            List[str] or None: The extracted documents, or an empty list or
            single document if an error occurred.
        """
        if query_results is None:
            return []

        if "documents" in query_results:
            documents = query_results["documents"]

            if len(documents) == 1 and isinstance(documents[0], list):
                try:
                    documents = [json.loads(doc) for doc in documents[0]]
                except Exception as e:
                    return documents[0]

            return documents

    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        return ChromaDB_VectorStore._extract_documents(
            self.sql_collection.query(
                query_texts=[question],
                n_results=self.n_results,
            )
        )

    def get_related_ddl(self, question: str, **kwargs) -> list:
        return ChromaDB_VectorStore._extract_documents(
            self.ddl_collection.query(
                query_texts=[question],
            )
        )

    def get_related_documentation(self, question: str, **kwargs) -> list:
        return ChromaDB_VectorStore._extract_documents(
            self.documentation_collection.query(
                query_texts=[question],
            )
        )
    def train(
        self,
        sql: dict = None,
        ddl: dict = None,
        documentation: dict = None,
        # plan: TrainingPlan = None,
    ) -> str:
        """
        **Example:**
        ```python
        db.train()
        ```

        Train Vanna.AI on a question and its corresponding SQL query.
        If you call it with no arguments, it will check if you connected to a database and it will attempt to train on the metadata of that database.
        If you call it with the sql argument, it's equivalent to [`db.add_question_sql()`][vanna.base.base.VannaBase.add_question_sql].
        If you call it with the ddl argument, it's equivalent to [`db.add_ddl()`][vanna.base.base.VannaBase.add_ddl].
        If you call it with the documentation argument, it's equivalent to [`db.add_documentation()`][vanna.base.base.VannaBase.add_documentation].
        Additionally, you can pass a [`TrainingPlan`][vanna.types.TrainingPlan] object. Get a training plan with [`db.get_training_plan_generic()`][vanna.base.base.VannaBase.get_training_plan_generic].

        Args:
            question (str): The question to train on.
            sql (str): The SQL query to train on.
            ddl (str):  The DDL statement.
            documentation (str): The documentation to train on.
            plan (TrainingPlan): The training plan to train on.
        """

        # if question and not sql:
        #     raise f"Please also provide a SQL query"

        if documentation:
            #print("Adding documentation....")
            return self.add_documentation(documentation)

        if sql:
            # if question is None:
                # question = self.generate_question(sql)
                # #print("Question generated with sql:", question, "\nAdding SQL...")
            return self.add_question_sql(sql)

        if ddl:
            #print("Adding ddl:", ddl)
            return self.add_ddl(ddl)
