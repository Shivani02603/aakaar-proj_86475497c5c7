import os
from .embeddings import get_embedding
from pgvector.psycopg2 import register_vector
import psycopg2
import google.generativeai as genai

def retrieve_context(query, top_k, session_id, user_id):
    """
    Embeds the query, retrieves the top-k relevant chunks from the vector store.
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

    # Generate query embedding
    query_embedding = get_embedding(query)

    # Retrieve top-k chunks by cosine similarity
    cursor.execute(
        """
        SELECT content, embedding
        FROM vector_store
        WHERE session_id = %s AND user_id = %s
        ORDER BY embedding <=> %s
        LIMIT %s
        """,
        (session_id, user_id, query_embedding, top_k)
    )
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    # Extract content and return
    return [row[0] for row in results]

def answer_question(query: str, session_id: str, user_id: str) -> dict:
    """
    Retrieves context, builds a prompt, and generates an answer using the runtime LLM.
    """
    # Retrieve context
    top_k = 5
    context_chunks = retrieve_context(query, top_k, session_id, user_id)
    context = "\n".join(context_chunks)

    # Build prompt
    prompt = f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"

    # Read API key for Google Gemini LLM
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=gemini_api_key)

    # Generate answer using Gemini-2.0-flash
    response = genai.generate_text(
        model="gemini-2.0-flash",
        prompt=prompt
    )

    # Extract answer and sources
    answer = response.result
    sources = context_chunks

    return {
        "answer": answer,
        "sources": sources
    }