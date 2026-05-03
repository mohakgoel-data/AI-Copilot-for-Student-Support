from fastapi import FastAPI, UploadFile, File, Depends
from sqlalchemy.orm import Session

from db import SessionLocal
from ingestion_pipeline.database_manager import sync_data_to_db
from ingestion_pipeline.parser import parse_document
from ingestion_pipeline.embeddings_pipeline import build_vector_records


import hashlib

app = FastAPI()


# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):

    # 1. Extract text
    text_data = parse_document(file.file)

    if not text_data or not text_data.strip():
        return {"error": "No text found in PDF"}

    # 2. Generate file hash
    file_hash = hashlib.sha256(text_data.encode()).hexdigest()

    # 3. Chunk text
    raw_chunks = text_data.split("\n\n")

    final_chunks = [
        {"content": chunk.strip(), "metadata": {"source": file.filename}}
        for chunk in raw_chunks if chunk.strip()
    ]

    # 4. Generate embeddings
    records = build_vector_records(final_chunks, file_hash)

    # 5. Store in DB
    doc_id = sync_data_to_db(db, file.filename, file_hash, records)

    return {
        "message": "Upload successful",
        "doc_id": doc_id,
        "total_chunks": len(records)
    }