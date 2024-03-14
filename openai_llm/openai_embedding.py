import os
import openai
from dotenv import load_dotenv
from chromadb.utils import embedding_functions

class OpenAI_Embeddings:
    def __init__(self, config=None):
        # Define the path for the .env file
        load_dotenv(dotenv_path='.env')

        # Initialize attributes
        self.api_key = None
        self.api_base = None
        self.api_type = None
        self.api_version = None
        self.model_name = None

        # Apply config if provided, otherwise load from environment
        if config is not None:
            self.apply_config(config)
        else:
            self.load_from_env()

        # Validate that necessary configurations are present
        self.validate_config()

        # Initialize the OpenAI client with the API key
        self.client = openai.AzureOpenAI(api_key = self.api_key,
                                         api_version = self.api_version,
                                         azure_endpoint = self.api_base)

    def apply_config(self, config):
        self.api_key = config.get('api_key')
        self.api_base = config.get('api_base')
        self.api_type = config.get('api_type')
        self.api_version = config.get('api_version')
        self.model_name = config.get('embedding_model_name')

    def load_from_env(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv("OPENAI_API_BASE")
        self.api_type = os.getenv("OPENAI_API_TYPE")
        self.api_version = os.getenv("OPENAI_API_VERSION")
        self.model_name = os.getenv("EMBEDDING_MODEL_NAME")

    def validate_config(self):
        if not self.api_key:
            raise ValueError("API key is required but not provided.")
        if not self.api_base:
            raise ValueError("API base is required but not provided.")
        if not self.model_name:
            raise ValueError("Model name is required but not provided.")

    def generate_embedding(self, data: str, **kwargs) -> list:
        # Determine the engine to use, fall back to a default if not specified
        engine = self.model_name if self.model_name else "text-embedding-ada-002"

        response = self.client.embeddings.create(
            model=self.model_name,
            input=[data],
            **kwargs
        )
        return response.data[0].embedding
    
    def chroma_embedding_function(self):
        # Initialize and return an OpenAIEmbeddingFunction instance with current configurations
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=self.api_key,
            api_base=self.api_base,
            api_type=self.api_type, 
            api_version=self.api_version,
            model_name=self.model_name
        )
        return openai_ef
