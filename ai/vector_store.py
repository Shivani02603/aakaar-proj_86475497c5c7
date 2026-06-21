import os
import psycopg2
from psycopg2.extras import Json
from typing import List, Dict, Any

def get_pg_connection():
    """
    Lazily initialize and return a PostgreSQL connection.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set.")
    return psycopg2.connect(db_url)

def upsert(id: str, vector: List[float], metadata: Dict[str, Any]):
    """
    Upsert a vector and its metadata into the pgvector table.
    """
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vectors (
                    id TEXT PRIMARY KEY,
                    embedding VECTOR(%s),
                    metadata JSONB
                );
            """, (len(vector),))
            cur.execute("""
                INSERT INTO vectors (id, embedding, metadata)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                SET embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata;
            """, (id, vector, Json(metadata)))
        conn.commit()
    finally:
        conn.close()

def search(query_embedding: List[float], top_k: int, **filters) -> List[Dict[str, Any]]:
    """
    Search for the top_k most similar vectors to the query_embedding.
    """
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            filter_conditions = []
            filter_values = []
            for key, value in filters.items():
                filter_conditions.append(f"metadata->>%s = %s")
                filter_values.extend([key, value])
            filter_clause = " AND ".join(filter_conditions)
            if filter_clause:
                filter_clause = f"WHERE {filter_clause}"
            
            query = f"""
                SELECT id, embedding, metadata, 1 - (embedding <=> %s) AS similarity
                FROM vectors
                {filter_clause}
                ORDER BY embedding <=> %s
                LIMIT %s;
            """
            cur.execute(query, [query_embedding, query_embedding, top_k] + filter_values)
            results = cur.fetchall()
            matches = [
                {"id": row[0], "embedding": row[1], "metadata": row[2], "similarity": row[3]}
                for row in results
            ]
        return matches
    finally:
        conn.close()