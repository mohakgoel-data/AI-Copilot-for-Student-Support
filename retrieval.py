import os
from google import genai
from sqlalchemy.orm import Session
from sqlalchemy import text
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_query_embedding(query_text: str):

    try:
        response = client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=query_text
        )

        return response.embeddings[0].values
    except Exception as e:
        print(f"Error generating query embedding: {e}")
        return None
    

def search_relevant_chunks(session: Session, query_vector: list, top_k: int = 6):

    vector_str = str(query_vector)

    sql = text("""
        SELECT 
            id, 
            document_id, 
            content, 
            metadata_json, 
            (embedding <=> :val) AS distance
        FROM document_chunks
        ORDER BY distance ASC
        LIMIT :limit
    """)

    try:
        result = session.execute(sql, {"val": vector_str, "limit": top_k})
        
        chunks = []
        for row in result:
            chunks.append({
                "chunk_id": row.id,
                "document_id": row.document_id,
                "content": row.content,
                "metadata": row.metadata_json,
                "score": 1 - row.distance
            })
        
        return chunks
    except Exception as e:
        print(f"Database search error: {e}")
        return []