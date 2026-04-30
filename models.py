from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from pgvector.sqlalchemy import Vector

Base = declarative_base()

#Table to store File Info

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)

    filename = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

#Table to store Chunks and Embeddings

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True)

    document_id = Column(Integer, ForeignKey("documents.id"))

    content = Column(Text, nullable=False)

    embedding = Column(Vector(1536))

    document = relationship("Document")

