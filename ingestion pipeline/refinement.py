import hashlib
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter

def refine_logical_blocks(logical_blocks: list, doc_id: str):


    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name="gpt-4",
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", "•", "!", "?", ". ", " "]
    )

    final_chunks = []


    for block_index, block in enumerate(logical_blocks):

        sub_texts = splitter.split_text(block["content"])
        

        for chunk_index, text in enumerate(sub_texts):
            clean_text = text.strip()
            if len(clean_text) < 50: 
                continue

            hash_input = f"{doc_id}-{clean_text}-{chunk_index}"
            chunk_hash = hashlib.sha256(hash_input.encode()).hexdigest()

            chunk_data = {
                "chunk_id": chunk_hash,
                "doc_id": doc_id,
                "content": clean_text,
                "metadata": {
                    **block["metadata"],
                    "chunk_index": chunk_index,
                    "parent_block_index": block_index
                }
            }
            final_chunks.append(chunk_data)
            
    return final_chunks