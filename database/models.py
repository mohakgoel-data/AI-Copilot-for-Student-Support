from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON # Add JSON here
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from pgvector.sqlalchemy import Vector
from sqlalchemy.sql import func

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True) 
    filename = Column(String, nullable=False)
    file_hash = Column(String, unique=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(64), primary_key=True) 
    
    document_id = Column(Integer, ForeignKey("documents.id"))
    content = Column(Text, nullable=False)
    
    embedding = Column(Vector(3072)) 

    metadata_json = Column(JSON) 

    document = relationship("Document")

class ChatMessage(Base):
    __tablename__ = 'chat_messages'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True) 
    role = Column(String)
    content = Column(Text)
    
    source_metadata = Column(JSONB, nullable=True) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())