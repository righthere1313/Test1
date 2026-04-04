from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.user_session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    teaching_subject = Column(String, nullable=True)
    teaching_style = Column(String, nullable=True)
    additional_info = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

