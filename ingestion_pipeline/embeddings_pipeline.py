import hashlib
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

import asyncio

TPM_LIMIT = 30000
AVG_TOKENS_PER_CHUNK = 200
SAFE_UTILIZATION = 0.8

MAX_CHUNKS_PER_BATCH = 90 #int(
#     (TPM_LIMIT * SAFE_UTILIZATION) / AVG_TOKENS_PER_CHUNK
# )

async def build_vector_records_safe(final_chunks, file_hash):
    batches = [
        final_chunks[i:i + MAX_CHUNKS_PER_BATCH]
        for i in range(0, len(final_chunks), MAX_CHUNKS_PER_BATCH)
    ]

    for i, batch in enumerate(batches):
        print(f"Processing batch {i+1}/{len(batches)}")

        contents = [chunk["content"] for chunk in batch]

        try:
            response = await asyncio.to_thread(
                client.models.embed_content,
                model="models/gemini-embedding-001",
                contents=contents
            )

            for chunk, emb in zip(batch, response.embeddings):
                chunk["embedding"] = emb.values

        except Exception as e:
            print(f"Batch {i+1} failed: {e}")
            raise Exception(f"Embedding pipeline failed at batch {i+1}")

        if i < len(batches) - 1:
            await asyncio.sleep(60)

    return final_chunks