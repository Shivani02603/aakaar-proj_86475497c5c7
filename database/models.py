from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, MetaData
from sqlalchemy.ext.declarative import declarative_base

# Define metadata and base for SQLAlchemy models
metadata = MetaData()
Base = declarative_base(metadata=metadata)

# User entity
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False)

# Session entity
class Session(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)

# UploadedFile entity
class UploadedFile(Base):
    __tablename__ = 'uploaded_files'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    uploaded_at = Column(DateTime, nullable=False)

# DocumentChunk entity
class DocumentChunk(Base):
    __tablename__ = 'document_chunks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey('uploaded_files.id'), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Text, nullable=False)  # Assuming embedding is stored as JSON or similar
    metadata = Column(Text, nullable=True)
    chunk_index = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)

# Message entity
class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    metadata = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)