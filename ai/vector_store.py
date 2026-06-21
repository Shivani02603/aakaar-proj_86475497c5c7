import os
import psycopg2
from psycopg2.extras import Json
from typing import List, Dict, Any

def get_pg_connection():
    """
    Lazily initializes and returns a PostgreSQL connection using environment variables.
    """
    db_host = os.getenv("PG_HOST")
    db_port = os.getenv("PG_PORT", "5432")
    db_name = os.getenv("PG_DATABASE")
    db_user = os.getenv("PG_USER")
    db_password = os.getenv("PG_PASSWORD")

    if not all([db_host, db_name, db_user, db_password]):
        raise ValueError("One or more PostgreSQL environment variables are not set.")

    return psycopg2.connect(
        host=db_host,
        port=db_port,
        dbname=db_name,
        user=db_user,
        password=db_password
    )

def upsert(id: str, vector: List[float], metadata: Dict[str, Any]):
    """
    Upserts a vector and its metadata into the pgvector table.
    """
    connection = get_pg_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO vectors (id, embedding, metadata)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                SET embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata;
            """, (id, vector, Json(metadata)))
        connection.commit()
    finally:
        connection.close()

def search(query_embedding: List[float], top_k: int, **filters) -> List[Dict[str, Any]]:
    """
    Searches for the top_k most similar vectors to the query_embedding in the pgvector table.
    """
    connection = get_pg_connection()
    try:
        with connection.cursor() as cursor:
            filter_conditions = []
            filter_values = []
            for key, value in filters.items():
                filter_conditions.append(f"metadata->>%s = %s")
                filter_values.extend([key, value])
            filter_query = " AND ".join(filter_conditions)

            query = f"""
                SELECT id, embedding, metadata, 1 - (embedding <=> %s) AS similarity
                FROM vectors
                {"WHERE " + filter_query if filter_query else ""}
                ORDER BY embedding <=> %s
                LIMIT %s;
            """
            cursor.execute(query, [query_embedding, query_embedding, top_k] + filter_values)
            results = cursor.fetchall()

        matches = [
            {
                "id": row[0],
                "embedding": row[1],
                "metadata": row[2],
                "similarity": row[3]
            }
            for row in results
        ]
        return matches
    finally:
        connection.close()