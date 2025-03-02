from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

load_dotenv()

# Use SQLite database
DATABASE_URL = "sqlite:///./gym_management.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a session factory with relationship loading support
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session  # This enables relationship loading features
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
