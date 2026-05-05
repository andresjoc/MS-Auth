from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.connection import Base


class AppUser(Base):
    __tablename__ = "app_user"

    id_user = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    birth_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    credential = relationship(
        "AuthCredential",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class AuthCredential(Base):
    __tablename__ = "auth_credential"

    id_credential = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_user = Column(Integer, ForeignKey("app_user.id_user"), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("AppUser", back_populates="credential")
