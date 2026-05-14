from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Header, APIRouter, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from database.db import SessionLocal
from database.database_manager import sync_data_to_db
from database.models import User
from ingestion_pipeline.parser import parse_document
from ingestion_pipeline.llama_index_pipeline import process_markdown
from ingestion_pipeline.refinement import refine_logical_blocks
from ingestion_pipeline.embeddings_pipeline import build_vector_records_safe
from generation import generate_response
from fastapi import HTTPException
from database.database_manager import delete_document
from fastapi.security import OAuth2PasswordRequestForm
from auth import get_current_user_data, TokenResponse, create_access_token, UserRegister,verify_password, get_current_user

from auth import hash_password, TokenResponse, create_access_token, UserRegister,verify_password, get_current_user
import os
from dotenv import load_dotenv
import hashlib

from contextlib import closing

from retrieval import get_query_embedding

from database.db import SessionLocal



load_dotenv()
app = FastAPI()

def warmup():
    print("Warming up AI pipeline...")
    try:
        get_query_embedding("hello")
        with closing(SessionLocal()) as db:
            db.execute("SELECT 1")
        print("Warmup complete.")
    except Exception as e:
        print(f"Warmup failed: {e}")


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
    return StreamingResponse(
        generate_response(db, query, user_id=user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

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

    logical_blocks = process_markdown(
    markdown_text=text_data,
    file_path=file.filename
    )
    final_chunks = refine_logical_blocks(logical_blocks, file_hash)

    records = await build_vector_records_safe(final_chunks, file_hash)

    doc_id = sync_data_to_db(db, file.filename, file_hash, records)

    return {
        "message": "Upload successful",
        "doc_id": doc_id,
        "total_chunks": len(records)
    }

@app.delete("/documents/{document_id}")
def remove_document(
    document_id: int,
    db: Session = Depends(get_db),
    user_data: dict = Depends(get_current_user)
):

    if not user_data.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail="Only admins can delete documents."
        )

    deleted_doc = delete_document(
        session=db,
        document_id=document_id
    )

    if not deleted_doc:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return {
        "message": "Document deleted successfully",
        "document_id": document_id,
        "filename": deleted_doc.filename
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
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == form_data.username
    ).first()
    if not user or not verify_password(
        form_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    token = create_access_token(
        data={
            "user_id": user.id,
            "is_admin": user.is_admin
        }
    )
    return {"access_token": token}

app.include_router(router)

ADMIN_CREATION_KEY = os.getenv("ADMIN_CREATION_KEY")

@router.post("/register-admin")
def register_admin(user_in: UserRegister, master_key: str, db: Session = Depends(get_db)):

    if master_key != ADMIN_CREATION_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid Master Key"
        )

    existing_user = db.query(User).filter(User.email == user_in.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = hash_password(user_in.password)
    new_admin = User(
        email=user_in.username,
        password_hash=hashed_password,
        is_admin=True
    )
    
    db.add(new_admin)
    db.commit()
    return {"message": "Admin account created successfully"}

app.include_router(router)


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
