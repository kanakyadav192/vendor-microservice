from sqlmodel import create_engine, Session
import os
from sqlalchemy.pool import NullPool

# Read DATABASE_URL from environment variables.
# For local development we will fall back to sqlite file.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

# Create database engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, echo=True)
else:
    # For PostgreSQL on Render or production
    engine = create_engine(DATABASE_URL, echo=True, poolclass=NullPool)

def create_db_and_tables():
    from .models import SQLModel
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
