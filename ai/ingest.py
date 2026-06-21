import os
import pandas as pd
from tiktoken import encoding_for_model
from .embeddings import get_embedding
from pgvector.psycopg2 import register_vector
import psycopg2

# Constants for chunking
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def chunk(document):
    """
    Splits a document into overlapping chunks using the 'recursive' strategy.
    """
    tokenizer = encoding_for_model("text-embedding-3-small")
    tokens = tokenizer.encode(document)
    chunks = []
    for i in range(0, len(tokens), CHUNK_SIZE - CHUNK_OVERLAP):
        chunk_tokens = tokens[i:i + CHUNK_SIZE]
        chunks.append(tokenizer.decode(chunk_tokens))
        if len(chunk_tokens) < CHUNK_SIZE:
            break
    return chunks

def ingest_excel(file_path, session_id, user_id):
    """
    Reads an Excel file, chunks its content, generates embeddings, and upserts into the vector store.
    """
    # Read database connection details from environment variables
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    # Connect to PostgreSQL database
    conn = psycopg2.connect(
        host=db_host,
        dbname=db_name,
        user=db_user,
        password=db_password
    )
    register_vector(conn)
    cursor = conn.cursor()

    # Read the Excel file
    excel_data = pd.ExcelFile(file_path)

    for sheet_name in excel_data.sheet_names:
        sheet_data = excel_data.parse(sheet_name)
        for column in sheet_data.columns:
            content = sheet_data[column].dropna().astype(str).str.cat(sep=" ")
            chunks = chunk(content)

            for chunk_text in chunks:
                embedding = get_embedding(chunk_text)
                cursor.execute(
                    """
                    INSERT INTO vector_store (session_id, user_id, content, embedding)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (content) DO UPDATE
                    SET embedding = EXCLUDED.embedding
                    """,
                    (session_id, user_id, chunk_text, embedding)
                )

    conn.commit()
    cursor.close()
    conn.close()