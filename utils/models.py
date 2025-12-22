from sqlalchemy import Column, String, DateTime, Integer, Boolean
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Photo(Base):
    __tablename__ = "photos"

    id = Column(String, primary_key=True, nullable=False)
    photoUrl = Column(String)
    createdAt = Column(DateTime, default=datetime.utcnow)
    like = Column(Integer, default=0)
    upload = Column(Boolean)