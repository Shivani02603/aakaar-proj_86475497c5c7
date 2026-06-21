import os
from .embeddings import get_embedding
from pgvector.psycopg2 import Vector
import psycopg2
import google.generativeai as genai

def retrieve_context(query: str, top_k: int, session_id: str, user_id: str):
    """
    Embeds the query, retrieves the top-k most relevant chunks from the vector store.
    """
    # Lazy load environment variables
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set.")

    # Connect to PostgreSQL with pgvector
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    # Embed the query
    query_embedding = get_embedding(query)

    # Retrieve top-k chunks by cosine similarity
    cursor.execute("""
        SELECT content
        FROM vectors
        WHERE session_id = %s AND user_id = %s
        ORDER BY embedding <=> %s
        LIMIT %s;
    """, (session_id, user_id, Vector(query_embedding), top_k))
    results = cursor.fetchall()

    # Close connection
    cursor.close()
    conn.close()

    # Extract content from results
    return [row[0] for row in results]

def answer_question(query: str, session_id: str, user_id: str) -> dict:
    """
    Retrieves context, builds a prompt, and generates an answer using the runtime LLM.
    """
    # Lazy load environment variables
    genai_api_key = os.getenv("GENAI_API_KEY")
    if not genai_api_key:
        raise ValueError("GENAI_API_KEY environment variable is not set.")
    genai.configure(api_key=genai_api_key)

    # Retrieve context
    context_chunks = retrieve_context(query, top_k=5, session_id=session_id, user_id=user_id)
    context = "\n".join(context_chunks)

    # Build the prompt
    prompt = f"Context:\n{context}\n\nQuestion:\n{query}\n\nAnswer:"

    # Generate answer using the runtime LLM
    response = genai.generate_text(model="gemini-2.0-flash", prompt=prompt)

    # Extract answer and sources
    answer = response.text.strip()
    sources = context_chunks

    return {"answer": answer, "sources": sources}