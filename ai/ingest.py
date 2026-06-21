import os
import pandas as pd
from tiktoken import Tokenizer
from .embeddings import get_embedding
from pgvector.psycopg2 import Vector
import psycopg2

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def chunk(document: str):
    """
    Splits the document into overlapping chunks using the recursive strategy.
    """
    tokenizer = Tokenizer()
    tokens = tokenizer.encode(document)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + CHUNK_SIZE, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append(tokenizer.decode(chunk_tokens))
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks

def ingest_excel(file_path: str, session_id: str, user_id: str):
    """
    Reads an Excel file, chunks its content, embeds the chunks, and upserts into the vector store.
    """
    # Lazy load environment variables
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set.")

    # Connect to PostgreSQL with pgvector
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    # Read Excel file
    excel_data = pd.ExcelFile(file_path)
    for sheet_name in excel_data.sheet_names:
        sheet_data = excel_data.parse(sheet_name)
        document = sheet_data.to_string(index=False)

        # Chunk the document
        chunks = chunk(document)

        # Embed and upsert each chunk
        for chunk_text in chunks:
            embedding = get_embedding(chunk_text)
            cursor.execute("""
                INSERT INTO document_chunks (session_id, file_id, content, embedding, metadata, chunk_index, created_at)
                VALUES (%s, NULL, %s, %s, NULL, NULL, NOW())
                ON CONFLICT (file_id, chunk_index)
                DO UPDATE SET embedding = EXCLUDED.embedding, content = EXCLUDED.content;
            """, (session_id, chunk_text, Vector(embedding)))

    # Commit and close connection
    conn.commit()
    cursor.close()
    conn.close()