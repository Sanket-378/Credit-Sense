from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import pdfplumber
import io
import json
from typing import List
from datetime import datetime
from groq import Groq
import os

from database import get_db, init_db, Document, User, SchemeRecommendation
from vector_service import vector_db
from scheme_scraper import get_recommended_schemes

app = FastAPI(title="Credit Sense API")

# Initialize Groq client - Use environment variable or default
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your_groq_api_key_here")
groq_client = Groq(api_key=GROQ_API_KEY)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def read_root():
    return {"message": "Credit Sense API is running", "version": "1.0"}

def extract_financial_data_with_groq(text: str) -> dict:
    """
    Use Groq AI to intelligently extract financial information from text
    """
    try:
        prompt = f"""
You are a financial document analyzer. Extract the following information from the given text.
If any field is not found, leave it as null or empty string.

Extract these fields:
- person_name: Full name of the person
- bank_account_number: Bank account number (numbers only)
- pan_card_number: PAN card number (format: XXXXX0000X)
- tax_payable: Tax amount payable
- company_name: Name of the company/employer
- job_role: Job title or designation
- salary: Salary amount (monthly or annual)
- address: Full address
- phone_number: Contact phone number
- email: Email address
- document_type: Type of document (e.g., Salary Slip, Bank Statement, Tax Return, etc.)

Return ONLY a valid JSON object with these exact field names. Do not include any explanation.

Text to analyze:
{text[:4000]}

JSON Output:"""

        response = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial document data extraction expert. Always return valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse JSON
        if result_text.startswith("```json"):
            result_text = result_text.replace("```json", "").replace("```", "").strip()
        elif result_text.startswith("```"):
            result_text = result_text.replace("```", "").strip()
            
        extracted_data = json.loads(result_text)
        return extracted_data
        
    except Exception as e:
        print(f"Groq extraction error: {str(e)}")
        return {
            "person_name": "",
            "bank_account_number": "",
            "pan_card_number": "",
            "tax_payable": "",
            "company_name": "",
            "job_role": "",
            "salary": "",
            "address": "",
            "phone_number": "",
            "email": "",
            "document_type": ""
        }

@app.post("/api/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = "default_user",
    db: Session = Depends(get_db)
):
    """
    Upload and process PDF document with AI extraction and vector storage
    """
    try:
        # Ensure user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            user = User(user_id=user_id, name="Default User")
            db.add(user)
            db.commit()
        
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Read file content
        content = await file.read()
        file_size = len(content) / 1024  # Size in KB
        
        # Process PDF with pdfplumber
        extracted_text = ""
        page_count = 0
        metadata = {}
        
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            page_count = len(pdf.pages)
            
            # Extract text from all pages
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n\n"
            
            # Get metadata
            if pdf.metadata:
                metadata = {
                    "author": pdf.metadata.get("Author", ""),
                    "creator": pdf.metadata.get("Creator", ""),
                    "producer": pdf.metadata.get("Producer", ""),
                    "creation_date": str(pdf.metadata.get("CreationDate", ""))
                }
        
        # Simple verification logic
        verification_status = "verified" if len(extracted_text) > 100 else "needs_review"
        
        # Extract financial data using Groq AI
        print("Extracting financial data with Groq AI...")
        financial_data = extract_financial_data_with_groq(extracted_text)
        
        # Save to database
        db_document = Document(
            user_id=user_id,
            filename=file.filename,
            file_type="PDF",
            extracted_text=extracted_text,
            page_count=page_count,
            file_size=file_size,
            verification_status=verification_status,
            doc_metadata=json.dumps(metadata),
            # Financial data
            person_name=financial_data.get("person_name", ""),
            bank_account_number=financial_data.get("bank_account_number", ""),
            pan_card_number=financial_data.get("pan_card_number", ""),
            tax_payable=financial_data.get("tax_payable", ""),
            company_name=financial_data.get("company_name", ""),
            job_role=financial_data.get("job_role", ""),
            salary=financial_data.get("salary", ""),
            address=financial_data.get("address", ""),
            phone_number=financial_data.get("phone_number", ""),
            email=financial_data.get("email", ""),
            document_type=financial_data.get("document_type", ""),
            additional_info=json.dumps(financial_data)
        )
        
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        # Add to vector database
        vector_db.add_user_financial_data(user_id, db_document.id, financial_data)
        
        # Return response
        return {
            "id": db_document.id,
            "filename": db_document.filename,
            "file_type": db_document.file_type,
            "page_count": page_count,
            "file_size": round(file_size, 2),
            "verification_status": verification_status,
            "extracted_text_preview": extracted_text[:500] if extracted_text else "No text extracted",
            "upload_date": db_document.upload_date.isoformat(),
            "metadata": metadata,
            "financial_data": {
                "person_name": financial_data.get("person_name", ""),
                "bank_account_number": financial_data.get("bank_account_number", ""),
                "pan_card_number": financial_data.get("pan_card_number", ""),
                "tax_payable": financial_data.get("tax_payable", ""),
                "company_name": financial_data.get("company_name", ""),
                "job_role": financial_data.get("job_role", ""),
                "salary": financial_data.get("salary", ""),
                "address": financial_data.get("address", ""),
                "phone_number": financial_data.get("phone_number", ""),
                "email": financial_data.get("email", ""),
                "document_type": financial_data.get("document_type", "")
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.get("/api/documents")
def get_documents(db: Session = Depends(get_db)):
    """
    Get all uploaded documents
    """
    documents = db.query(Document).order_by(Document.upload_date.desc()).all()
    
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "page_count": doc.page_count,
            "file_size": doc.file_size,
            "verification_status": doc.verification_status,
            "upload_date": doc.upload_date.isoformat(),
            "extracted_text_preview": doc.extracted_text[:200] if doc.extracted_text else "",
            "document_type": doc.document_type or "Unknown",
            "person_name": doc.person_name or "",
            "company_name": doc.company_name or ""
        }
        for doc in documents
    ]

@app.get("/api/documents/{document_id}")
def get_document(document_id: int, db: Session = Depends(get_db)):
    """
    Get a specific document by ID with all extracted financial data
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": document.id,
        "filename": document.filename,
        "file_type": document.file_type,
        "page_count": document.page_count,
        "file_size": document.file_size,
        "verification_status": document.verification_status,
        "upload_date": document.upload_date.isoformat(),
        "extracted_text": document.extracted_text,
        "metadata": json.loads(document.doc_metadata) if document.doc_metadata else {},
        "financial_data": {
            "person_name": document.person_name or "",
            "bank_account_number": document.bank_account_number or "",
            "pan_card_number": document.pan_card_number or "",
            "tax_payable": document.tax_payable or "",
            "company_name": document.company_name or "",
            "job_role": document.job_role or "",
            "salary": document.salary or "",
            "address": document.address or "",
            "phone_number": document.phone_number or "",
            "email": document.email or "",
            "document_type": document.document_type or ""
        }
    }

@app.delete("/api/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """
    Delete a document
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}

@app.post("/api/recommend-schemes")
async def recommend_schemes(
    query: str,
    user_id: str = "default_user",
    db: Session = Depends(get_db)
):
    """
    Get AI-powered scheme recommendations based on user query and profile
    """
    try:
        # Get user profile from vector database
        user_profile = vector_db.get_user_profile(user_id)
        
        # Get recommended schemes
        schemes = get_recommended_schemes(query, user_profile)
        
        # Save recommendations to database
        for scheme in schemes:
            recommendation = SchemeRecommendation(
                user_id=user_id,
                query=query,
                scheme_name=scheme['name'],
                scheme_description=scheme['description'],
                eligibility=scheme['eligibility'],
                benefits=scheme['benefits'],
                source_url=scheme['source_url'],
                relevance_score=scheme['relevance_score']
            )
            db.add(recommendation)
        
        db.commit()
        
        return {
            "query": query,
            "user_profile": user_profile,
            "schemes": schemes,
            "total_schemes": len(schemes)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recommendations: {str(e)}")

@app.get("/api/user-profile/{user_id}")
def get_user_profile(user_id: str):
    """
    Get user's financial profile from vector database
    """
    try:
        profile = vector_db.get_user_profile(user_id)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching profile: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
