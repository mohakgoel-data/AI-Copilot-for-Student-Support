from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from database.models import Document, DocumentChunk
from database.models import ChatMessage

def sync_data_to_db(session: Session, filename: str, file_hash: str, chunk_records: list):
    try:
        doc = session.query(Document).filter_by(file_hash=file_hash).first()
        
        if not doc:
            doc = Document(filename=filename, file_hash=file_hash)
            session.add(doc)
            session.flush() 

        for record in chunk_records:
            stmt = pg_insert(DocumentChunk).values(
                id=record["chunk_id"],
                document_id=doc.id,
                content=record["content"],
                embedding=record["embedding"],
                metadata_json=record["metadata"]
            )

            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_={
                    "content": stmt.excluded.content,
                    "embedding": stmt.excluded.embedding,
                    "metadata_json": stmt.excluded.metadata_json
                }
            )
            session.execute(upsert_stmt)
        
        session.commit()
        print(f"✅ Sync Complete: {filename}")
        return doc.id

    except Exception as e:
        session.rollback()
        print(f"❌ Sync Failed: {e}")
        raise e 

    finally:
        session.close()

def save_message(session, user_id, role, content, source_metadata=None):
    try:
        message = ChatMessage(
            user_id=user_id,
            role=role,
            content=content,
            source_metadata=source_metadata
        )

        session.add(message)
        session.commit()
        session.refresh(message) 
        return message

    except Exception as e:
        session.rollback()
        print(f"Failed to save message to DB: {e}")
        return None
    

def delete_document(session, document_id: int):

    document = (
        session.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if not document:
        return None

    session.delete(document)
    session.commit()
    return document