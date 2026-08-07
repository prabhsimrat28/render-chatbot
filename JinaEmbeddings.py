from langchain_core.embeddings import Embeddings
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

class JinaEmbeddings(Embeddings):
    def __init__(self,api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.jina.ai/v1"
        )
        self.model="jina-embeddings-v5-text-small"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        
        return response.data[0].embedding