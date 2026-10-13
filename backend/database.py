from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./credit_sense.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    name = Column(String)
    email = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    documents = relationship("Document", back_populates="user")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    filename = Column(String, index=True)
    file_type = Column(String)
    upload_date = Column(DateTime, default=datetime.utcnow)
    extracted_text = Column(Text)
    page_count = Column(Integer)
    file_size = Column(Float)
    verification_status = Column(String, default="pending")
    doc_metadata = Column(Text)
    
    # Extracted Financial Information
    person_name = Column(String)
    bank_account_number = Column(String)
    pan_card_number = Column(String)
    tax_payable = Column(String)
    company_name = Column(String)
    job_role = Column(String)
    salary = Column(String)
    address = Column(Text)
    phone_number = Column(String)
    email = Column(String)
    document_type = Column(String)
    additional_info = Column(Text)
    
    user = relationship("User", back_populates="documents")

class SchemeRecommendation(Base):
    __tablename__ = "scheme_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    query = Column(String)
    scheme_name = Column(String)
    scheme_description = Column(Text)
    eligibility = Column(Text)
    benefits = Column(Text)
    source_url = Column(String)
    relevance_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
