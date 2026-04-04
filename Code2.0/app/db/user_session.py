from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Ensure the directory exists
os.makedirs("data/db", exist_ok=True)

SQLALCHEMY_DATABASE_URI = "sqlite:///./data/db/users.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

from app.models import user as _user_model

Base.metadata.create_all(bind=engine)

def get_user_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
