from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.connection import Base


class Country(Base):
    __tablename__ = "country"

    id_country = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)


class Region(Base):
    __tablename__ = "region"

    id_region = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_country = Column(Integer, ForeignKey("country.id_country"), nullable=False)
    name = Column(String(100), nullable=False)


class City(Base):
    __tablename__ = "city"

    id_city = Column(Integer, primary_key=True, index=True)
    id_region = Column(Integer, ForeignKey("region.id_region"), nullable=False)
    name = Column(String(100), nullable=False)

    users = relationship("AppUser", back_populates="city")


class AppUser(Base):
    __tablename__ = "app_user"

    id_user = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_city = Column(Integer, ForeignKey("city.id_city"), nullable=False)
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
    city = relationship("City", back_populates="users")


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
