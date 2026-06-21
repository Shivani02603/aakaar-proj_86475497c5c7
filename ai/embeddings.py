import os
from typing import List
import openai

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

def embed_text(text: str) -> List[float]:
    """
    Embed a single piece of text using OpenAI's text-embedding-3-small model.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    
    openai.api_key = api_key
    response = openai.Embedding.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    embedding = response['data'][0]['embedding']
    if len(embedding) != EMBEDDING_DIM:
        raise ValueError(f"Embedding dimension mismatch. Expected {EMBEDDING_DIM}, got {len(embedding)}.")
    return embedding

def embed_batch(texts: List[str]) -> List[List[float]]:
    """
    Embed a batch of texts using OpenAI's text-embedding-3-small model.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    
    openai.api_key = api_key
    response = openai.Embedding.create(
        model=EMBEDDING_MODEL,
        input=texts
    )
    embeddings = [item['embedding'] for item in response['data']]
    for embedding in embeddings:
        if len(embedding) != EMBEDDING_DIM:
            raise ValueError(f"Embedding dimension mismatch. Expected {EMBEDDING_DIM}, got {len(embedding)}.")
    return embeddings

def get_embedding(texts: List[str]) -> List[List[float]]:
    """
    Module-level function to embed a batch of texts.
    """
    return embed_batch(texts)