
import hashlib
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def build_vector_records(final_chunks, doc_id):
    records = []

    contents = [chunk["content"] for chunk in final_chunks]
   
    response = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=contents
    )

    embeddings = [emb.values for emb in response.embeddings]

    for index, (chunk, embedding) in enumerate(zip(final_chunks, embeddings)):
        content = chunk["content"]
        metadata = chunk["metadata"]

        hash_input = f"{doc_id}-{index}-{content}"
        chunk_id = hashlib.sha256(hash_input.encode()).hexdigest()

        record = {
            "chunk_id": chunk_id,
            "content": content,
            "embedding": embedding,
            "metadata": metadata
        }

        records.append(record)

    return records