from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

# Drop sequences if they exist
with engine.connect() as conn:
    conn.execute(text("DROP SEQUENCE IF EXISTS members_id_seq CASCADE"))
    conn.execute(text("DROP SEQUENCE IF EXISTS attendances_id_seq CASCADE"))
    conn.execute(text("DROP SEQUENCE IF EXISTS payments_id_seq CASCADE"))
    conn.execute(text("DROP SEQUENCE IF EXISTS admins_id_seq CASCADE"))
    conn.commit()

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
