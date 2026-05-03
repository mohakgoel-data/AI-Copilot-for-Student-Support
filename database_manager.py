from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from models import Document, DocumentChunk

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