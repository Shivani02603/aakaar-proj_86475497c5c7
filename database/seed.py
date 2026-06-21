import asyncio
import uuid
from sqlalchemy.exc import SQLAlchemyError
from database.models import (
    SessionLocal,
    User,
    Session,
    UploadedFile,
    DocumentChunk,
    Message,
)


async def seed_database():
    async with SessionLocal() as session:
        try:
            # Insert Users
            user1 = User(id=uuid.uuid4(), email="user1@example.com")
            user2 = User(id=uuid.uuid4(), email="user2@example.com")
            user3 = User(id=uuid.uuid4(), email="user3@example.com")
            session.add_all([user1, user2, user3])
            await session.flush()

            # Insert Sessions
            session1 = Session(id=uuid.uuid4(), user_id=user1.id, name="Session 1")
            session2 = Session(id=uuid.uuid4(), user_id=user2.id, name="Session 2")
            session3 = Session(id=uuid.uuid4(), user_id=user3.id, name="Session 3")
            session.add_all([session1, session2, session3])
            await session.flush()

            # Insert UploadedFiles
            file1 = UploadedFile(
                id=uuid.uuid4(),
                session_id=session1.id,
                filename="file1.xlsx",
                original_filename="original_file1.xlsx",
                file_size=1024,
                status="uploaded",
                uploaded_at="2023-10-01 12:00:00"
            )
            file2 = UploadedFile(
                id=uuid.uuid4(),
                session_id=session2.id,
                filename="file2.xlsx",
                original_filename="original_file2.xlsx",
                file_size=2048,
                status="uploaded",
                uploaded_at="2023-10-01 12:00:00"
            )
            file3 = UploadedFile(
                id=uuid.uuid4(),
                session_id=session3.id,
                filename="file3.xlsx",
                original_filename="original_file3.xlsx",
                file_size=4096,
                status="uploaded",
                uploaded_at="2023-10-01 12:00:00"
            )
            session.add_all([file1, file2, file3])
            await session.flush()

            # Insert DocumentChunks
            chunk1 = DocumentChunk(
                id=uuid.uuid4(),
                file_id=file1.id,
                content="Chunk 1 content",
                embedding=[0.1] * 1536,
                metadata={"key": "value1"},
                chunk_index=1,
                created_at="2023-10-01 12:00:00"
            )
            chunk2 = DocumentChunk(
                id=uuid.uuid4(),
                file_id=file2.id,
                content="Chunk 2 content",
                embedding=[0.2] * 1536,
                metadata={"key": "value2"},
                chunk_index=2,
                created_at="2023-10-01 12:00:00"
            )
            chunk3 = DocumentChunk(
                id=uuid.uuid4(),
                file_id=file3.id,
                content="Chunk 3 content",
                embedding=[0.3] * 1536,
                metadata={"key": "value3"},
                chunk_index=3,
                created_at="2023-10-01 12:00:00"
            )
            session.add_all([chunk1, chunk2, chunk3])
            await session.flush()

            # Insert Messages
            message1 = Message(
                id=uuid.uuid4(),
                session_id=session1.id,
                role="user",
                content="User message 1",
                metadata={"sentiment": "positive"},
                created_at="2023-10-01 12:00:00"
            )
            message2 = Message(
                id=uuid.uuid4(),
                session_id=session2.id,
                role="assistant",
                content="Assistant message 2",
                metadata={"sentiment": "neutral"},
                created_at="2023-10-01 12:00:00"
            )
            message3 = Message(
                id=uuid.uuid4(),
                session_id=session3.id,
                role="system",
                content="System message 3",
                metadata={"sentiment": "negative"},
                created_at="2023-10-01 12:00:00"
            )
            session.add_all([message1, message2, message3])
            await session.commit()

            print("Database seeded successfully.")

        except SQLAlchemyError as e:
            await session.rollback()
            print(f"Error seeding database: {e}")


if __name__ == "__main__":
    asyncio.run(seed_database())