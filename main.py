from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Header, APIRouter, status
from sqlalchemy.orm import Session

from database.db import SessionLocal
from database.database_manager import sync_data_to_db
from database.models import User
from ingestion_pipeline.parser import parse_document
from ingestion_pipeline.embeddings_pipeline import build_vector_records
from generation import generate_response
from auth import get_current_user_data, TokenResponse, create_access_token, UserRegister,verify_password, get_current_user

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

@app.post("/chat")
def chat(
    query: str, 
    db: Session = Depends(get_db), 
    user_data: dict = Depends(get_current_user) 
):
    user_id = user_data["user_id"]
    return generate_response(db, query, user_id=user_id)

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db),user_data: dict = Depends(get_current_user)):

    if not user_data.get("is_admin"):
        raise HTTPException(status_code=403, detail="Only admins can upload documents.")
    
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

router = APIRouter(
    prefix="/auth", # This adds '/auth' to the start of all these routes
    tags=["Authentication"]
)

@router.post("/guest", response_model=TokenResponse)
def create_guest_user(db: Session = Depends(get_db)):

    new_user = User(email=None, password_hash=None, is_admin=False)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    token = create_access_token(data={"user_id": new_user.id, "is_admin": False})
    return {"access_token": token}

@router.post("/login", response_model=TokenResponse)
def login(user_in: UserRegister, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    
    # Verify password against the 'blender' result in DB
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Issue token with their real ID and Admin status
    token = create_access_token(data={"user_id": user.id, "is_admin": user.is_admin})
    return {"access_token": token}

app.include_router(router)