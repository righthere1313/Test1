import hashlib
import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin

logger = logging.getLogger(__name__)

from app.services.knowledge_base_service import LocalHashEmbeddings


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.vector_store = self._init_vector_store()

    def _init_vector_store(self):
        embeddings = self._build_embeddings()
        return Chroma(
            collection_name="user_profiles",
            persist_directory=settings.CHROMA_DB_DIR,
            embedding_function=embeddings,
        )

    def _build_embeddings(self) -> Any:
        # Copied logic from KnowledgeBaseService to ensure consistency
        if settings.USE_LOCAL_EMBEDDING:
            return LocalHashEmbeddings()
        try:
            embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
            # Test it
            embeddings.embed_query("test")
            return embeddings
        except Exception:
            logger.warning("Fallback to LocalHashEmbeddings")
            return LocalHashEmbeddings()

    def get_password_hash(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.get_password_hash(plain_password) == hashed_password

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def register_user(self, user_in: UserCreate) -> User:
        # 1. Check if user exists
        if self.get_user_by_username(user_in.username):
            raise ValueError("Username already registered")

        # 2. Create DB User
        hashed_password = self.get_password_hash(user_in.password)
        db_user = User(
            username=user_in.username,
            password_hash=hashed_password,
            teaching_subject=user_in.teaching_subject,
            teaching_style=user_in.teaching_style,
            additional_info=user_in.additional_info
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        # 3. Vectorize Profile
        self._vectorize_user_profile(db_user)

        return db_user

    def _vectorize_user_profile(self, user: User):
        lines = [f"User Profile: {user.username}"]
        if user.teaching_subject:
            lines.append(f"Teaching Subject: {user.teaching_subject}")
        if user.teaching_style:
            lines.append(f"Teaching Style: {user.teaching_style}")
        if user.additional_info:
            lines.append(f"Additional Info: {user.additional_info}")
        profile_text = "\n".join(lines)

        doc = Document(
            page_content=profile_text,
            metadata={
                "user_id": user.id,
                "username": user.username,
                "type": "user_profile"
            }
        )

        self.vector_store.add_documents([doc], ids=[f"user_{user.username}"])

    def authenticate_user(self, user_in: UserLogin) -> Optional[User]:
        user = self.get_user_by_username(user_in.username)
        if not user:
            return None
        if not self.verify_password(user_in.password, user.password_hash):
            return None
        return user
