import hashlib
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def build_vector_records(final_chunks):
    records = []

    for chunk in final_chunks:
        content = chunk["content"]
        metadata = chunk["metadata"]

        
        chunk_id = hashlib.sha256(content.encode()).hexdigest()

        
        response = client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=content
        )

        embedding = response.embeddings[0].values

        
        record = {
            "chunk_id": chunk_id,
            "content": content,
            "embedding": embedding,
            "metadata": metadata
        }

        records.append(record)

    return records