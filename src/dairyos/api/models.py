from sqlalchemy import Column, Integer, String, Date, Text
from .database import Base

class AnimalDB(Base):
    __tablename__ = "animals"
    
    id = Column(Integer, primary_key=True, index=True)
    tag = Column(String, unique=True, index=True)
    name = Column(String)
    status = Column(String)

class AIRecordDB(Base):
    __tablename__ = "ai_records"
    
    id = Column(Integer, primary_key=True, index=True)
    cow_id = Column(String, index=True)
    bull_id = Column(String)
    date = Column(Date)
    technician = Column(String)
    notes = Column(Text, nullable=True)
