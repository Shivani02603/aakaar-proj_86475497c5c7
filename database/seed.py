import uuid
from sqlalchemy.exc import SQLAlchemyError
from database.models import (
    engine,
    SessionLocal,
    User,
    Session,
    UploadedFile,
    DocumentChunk,
    Message
)

def seed_database():
    session = SessionLocal()
    try:
        # Insert Users
        user1 = User(id=uuid.uuid4(), email="user1@example.com")
        user2 = User(id=uuid.uuid4(), email="user2@example.com")
        user3 = User(id=uuid.uuid4(), email="user3@example.com")
        session.add_all([user1, user2, user3])
        session.flush()  # Flush to generate IDs for FK references

        # Insert Sessions
        session1 = Session(id=uuid.uuid4(), user_id=user1.id, name="Session 1")
        session2 = Session(id=uuid.uuid4(), user_id=user2.id, name="Session 2")
        session3 = Session(id=uuid.uuid4(), user_id=user3.id, name="Session 3")
        session.add_all([session1, session2, session3])
        session.flush()

        # Insert UploadedFiles
        file1 = UploadedFile(
            id=uuid.uuid4(),
            session_id=session1.id,
            filename="file1.txt",
            original_filename="original_file1.txt",
            file_size=1024,
            status="processed",
            uploaded_at=func.now()
        )
        file2 = UploadedFile(
            id=uuid.uuid4(),
            session_id=session2.id,
            filename="file2.txt",
            original_filename="original_file2.txt",
            file_size=2048,
            status="processed",
            uploaded_at=func.now()
        )
        file3 = UploadedFile(
            id=uuid.uuid4(),
            session_id=session3.id,
            filename="file3.txt",
            original_filename="original_file3.txt",
            file_size=4096,
            status="uploaded",
            uploaded_at=func.now()
        )
        session.add_all([file1, file2, file3])
        session.flush()

        # Insert DocumentChunks
        chunk1 = DocumentChunk(
            id=uuid.uuid4(),
            file_id=file1.id,
            content="This is the content of chunk 1.",
            embedding=[0.1] * 1536,
            metadata={"type": "text"},
            chunk_index=0,
            created_at=func.now()
        )
        chunk2 = DocumentChunk(
            id=uuid.uuid4(),
            file_id=file2.id,
            content="This is the content of chunk 2.",
            embedding=[0.2] * 1536,
            metadata={"type": "text"},
            chunk_index=1,
            created_at=func.now()
        )
        chunk3 = DocumentChunk(
            id=uuid.uuid4(),
            file_id=file3.id,
            content="This is the content of chunk 3.",
            embedding=[0.3] * 1536,
            metadata={"type": "text"},
            chunk_index=2,
            created_at=func.now()
        )
        session.add_all([chunk1, chunk2, chunk3])
        session.flush()

        # Insert Messages
        message1 = Message(
            id=uuid.uuid4(),
            session_id=session1.id,
            role="user",
            content="Hello, assistant!",
            metadata={"sentiment": "positive"},
            created_at=func.now()
        )
        message2 = Message(
            id=uuid.uuid4(),
            session_id=session2.id,
            role="assistant",
            content="How can I help you?",
            metadata={"sentiment": "neutral"},
            created_at=func.now()
        )
        message3 = Message(
            id=uuid.uuid4(),
            session_id=session3.id,
            role="system",
            content="Session initialized.",
            metadata={"status": "active"},
            created_at=func.now()
        )
        session.add_all([message1, message2, message3])

        # Commit the transaction
        session.commit()
        print("Database seeded successfully!")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error seeding database: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()