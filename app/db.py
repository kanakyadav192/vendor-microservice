# app/db.py
import os
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import NullPool

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

if DATABASE_URL.startswith("sqlite"):
    # SQLite needs the check_same_thread connect arg
    engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
else:
    # For postgres / production use NullPool to avoid connection pinning in some platforms
    engine = create_engine(DATABASE_URL, echo=False, poolclass=NullPool)

def create_db_and_tables() -> None:
    # Import models so SQLModel.metadata knows about them
    # avoid circular imports by importing inside the function
    from . import models  # noqa: F401
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

