from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON # Add JSON here
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True) 
    filename = Column(String, nullable=False)
    file_hash = Column(String, unique=True) 
    created_at = Column(DateTime, default=datetime.utcnow)

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(64), primary_key=True) 
    
    document_id = Column(Integer, ForeignKey("documents.id"))
    content = Column(Text, nullable=False)
    
    embedding = Column(Vector(3072)) 

    metadata_json = Column(JSON) 

    document = relationship("Document")