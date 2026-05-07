from fastapi import FastAPI, UploadFile, File, Depends
from sqlalchemy.orm import Session

from database.db import SessionLocal
from database.database_manager import sync_data_to_db
from ingestion_pipeline.parser import parse_document
from ingestion_pipeline.embeddings_pipeline import build_vector_records
from generation import generate_response


import hashlib

app = FastAPI()

MAX_FILE_SIZE = 10 * 1024 * 1024


# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        return {
            "error": "PDF exceeds maximum allowed size of 10 MB."
        }
    
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    file.file.seek(0)

    text_data = parse_document(file.file)

    if not text_data or not text_data.strip():
        return {"error": "No text found in PDF"}

    from ingestion_pipeline.llama_index_pipeline import process_markdown

    final_chunks = process_markdown(
    markdown_text=text_data,
    file_path=file.filename
    )

    records = build_vector_records(final_chunks, file_hash)

    doc_id = sync_data_to_db(db, file.filename, file_hash, records)

    return {
        "message": "Upload successful",
        "doc_id": doc_id,
        "total_chunks": len(records)
    }

@app.post("/ask")
def ask_question(student_query: str, db: Session = Depends(get_db)):

    return generate_response(
        session=db,
        student_query=student_query
    )