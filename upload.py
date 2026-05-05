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

    # 1. Generate file hash from original PDF bytes
    file_bytes = await file.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # Reset file pointer so parser can read the file
    file.file.seek(0)

    # 2. Extract text
    text_data = parse_document(file.file)

    if not text_data or not text_data.strip():
        return {"error": "No text found in PDF"}

   # 3. Create logical chunks using markdown pipeline
    from ingestion_pipeline.llama_index_pipeline import process_markdown

    final_chunks = process_markdown(
    markdown_text=text_data,
    file_path=file.filename
    )

    # 4. Generate embeddings
    records = build_vector_records(final_chunks, file_hash)

    # 5. Store in DB
    doc_id = sync_data_to_db(db, file.filename, file_hash, records)

    return {
        "message": "Upload successful",
        "doc_id": doc_id,
        "total_chunks": len(records)
    }