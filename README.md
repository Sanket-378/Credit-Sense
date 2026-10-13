# 🏦 Credit Sense - AI-Powered Financial Assessment Platform

**An intelligent financial document processing and government scheme recommendation system powered by AI.**

![Credit Sense](https://img.shields.io/badge/AI-Powered-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![React](https://img.shields.io/badge/React-18.3-61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688)
![License](https://img.shields.io/badge/License-Academic-orange)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Usage Guide](#usage-guide)
- [Team](#team)

---

## 🌟 Overview

**Credit Sense** is an AI-powered platform designed to help individuals and small businesses with limited credit history access suitable financial support. The system combines:

- **Document Verification**: OCR and AI-powered extraction from financial PDFs
- **Financial Health Analysis**: GenAI-powered insights from uploaded documents
- **Credit Risk Assessment**: Machine learning-based evaluation
- **Scheme Recommendations**: Intelligent matching with government schemes based on user profile

### 🎯 Problem Statement

Many individuals face difficulties accessing financial support due to:
- Scattered financial information
- Complex government schemes
- Lack of personalized guidance
- Limited credit history

### 💡 Solution

Credit Sense provides:
1. **Automated document processing** with AI extraction
2. **Vector database storage** for personalized user profiles
3. **Intelligent scheme recommendations** based on income, job, and needs
4. **Beautiful, intuitive interface** for easy navigation

---

## ✨ Features

### 🤖 AI-Powered Document Processing
- **PDF Upload**: Drag-and-drop interface
- **Intelligent Extraction**: Groq AI (Llama 3.1 70B) extracts:
  - Person Name
  - Bank Account Number
  - PAN Card Number
  - Tax Payable
  - Company Name & Job Role
  - Salary Information
  - Contact Details (Email, Phone, Address)
  - Document Type Classification

### 💾 Smart Data Storage
- **SQLite Database**: Structured storage with 11+ financial data columns
- **Vector Database (ChromaDB)**: User-specific collections for semantic search
- **Data Isolation**: Each user has separate vector collection

### 🎯 Intelligent Scheme Recommendations
- **Context-Aware Search**: Understands queries like "home loan", "business loan"
- **Profile Matching**: Analyzes user income, job, location
- **AI Ranking**: Groq AI ranks schemes by relevance (80%+ threshold)
- **12+ Government Schemes**: PMAY, MUDRA, Education loans, Pension schemes, etc.

### 🎨 Beautiful UI
- **Financial Theme**: Green (banking), Gold (premium), Blue (trust) color scheme
- **Responsive Design**: Works on all screen sizes
- **Interactive Elements**: Hover effects, smooth transitions
- **Two Main Pages**:
  - 📄 **Documents**: Upload and manage financial documents
  - 🎯 **Schemes**: Search and discover government schemes

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.109
- **AI/ML**: Groq AI (Llama 3.1 70B), Sentence Transformers
- **Document Processing**: pdfplumber (OCR)
- **Vector Database**: ChromaDB 0.4.22
- **Database**: SQLite with SQLAlchemy ORM
- **Web Scraping**: BeautifulSoup4, Requests
- **Server**: Uvicorn

### Frontend
- **Framework**: React 18.3
- **Build Tool**: Vite 6.0
- **Icons**: Lucide React
- **Styling**: Custom CSS with financial theme

### AI & Data
- **LLM**: Groq API with Llama 3.1 70B model
- **Vector Embeddings**: Sentence Transformers
- **Data Extraction**: JSON-based structured output
- **Semantic Search**: ChromaDB similarity search

---

## 📥 Installation

### Prerequisites

- **Python**: 3.8 or higher
- **Node.js**: 16 or higher
- **npm**: 7 or higher
- **Git**: Latest version

### Clone Repository

```bash
git clone https://github.com/Sanket-378/Credit-Sense.git
cd Credit-Sense
git checkout pranav-dev
```

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   Or using virtual environment (recommended):
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

3. **Dependencies installed**:
   - FastAPI, Uvicorn
   - pdfplumber (PDF processing)
   - Groq (AI LLM)
   - ChromaDB (Vector database)
   - SQLAlchemy (Database ORM)
   - BeautifulSoup4 (Web scraping)
   - Sentence Transformers (Embeddings)

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd ../frontend
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **Dependencies installed**:
   - React, React-DOM
   - Vite (Build tool)
   - Lucide React (Icons)

---

## 🚀 How to Run

### Method 1: Manual Start (Recommended)

#### Start Backend Server

1. Open terminal/PowerShell
2. Navigate to backend directory:
   ```bash
   cd backend
   ```
3. Run the server:
   ```bash
   python main.py
   ```
4. Backend will start on: **http://localhost:8000**
5. API Documentation: **http://localhost:8000/docs**

#### Start Frontend Server

1. Open **new** terminal/PowerShell
2. Navigate to frontend directory:
   ```bash
   cd frontend
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
4. Frontend will start on: **http://localhost:3000**

### Method 2: Using PowerShell Script (Windows)

```powershell
.\start-servers.ps1
```

This will open two terminal windows for backend and frontend.

---

## 📁 Project Structure

```
Credit-Sense/
├── backend/
│   ├── main.py                 # FastAPI application & API endpoints
│   ├── database.py             # SQLite database models & schemas
│   ├── vector_service.py       # ChromaDB vector database service
│   ├── scheme_scraper.py       # Scheme filtering & AI ranking
│   ├── requirements.txt        # Python dependencies
│   ├── credit_sense.db         # SQLite database (auto-created)
│   └── chroma_db/              # Vector database storage (auto-created)
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── DocumentUpload.jsx      # Document upload & management
│   │   │   └── SchemeRecommendations.jsx  # Scheme search & display
│   │   ├── App.jsx             # Main app with navigation
│   │   ├── main.jsx            # React entry point
│   │   └── index.css           # Custom financial-themed styles
│   ├── public/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── README.md                   # This file
├── README_SETUP.md            # Detailed setup guide
└── start-servers.ps1          # Quick start script (Windows)
```

---

## 🔌 API Endpoints

### Document Management

#### Upload Document
```http
POST /api/upload-document?user_id=default_user
Content-Type: multipart/form-data

Body: PDF file
```

**Response**:
```json
{
  "id": 1,
  "filename": "salary_slip.pdf",
  "page_count": 2,
  "file_size": 145.32,
  "verification_status": "verified",
  "financial_data": {
    "person_name": "John Doe",
    "salary": "₹80,000/month",
    "company_name": "Tech Corp",
    "pan_card_number": "ABCDE1234F",
    ...
  }
}
```

#### Get All Documents
```http
GET /api/documents
```

#### Get Document Details
```http
GET /api/documents/{id}
```

#### Delete Document
```http
DELETE /api/documents/{id}
```

### Scheme Recommendations

#### Get Recommendations
```http
POST /api/recommend-schemes?query=home loan&user_id=default_user
```

**Response**:
```json
{
  "query": "home loan",
  "user_profile": {
    "person_name": "John Doe",
    "salary": "₹80,000/month",
    "company_name": "Tech Corp",
    "total_documents": 2
  },
  "schemes": [
    {
      "name": "Pradhan Mantri Awas Yojana",
      "relevance_score": 0.95,
      "description": "...",
      "eligibility": "...",
      "benefits": "...",
      "source_url": "..."
    }
  ]
}
```

#### Get User Profile
```http
GET /api/user-profile/{user_id}
```

---

## 📖 Usage Guide

### Step 1: Upload Financial Documents

1. Open **http://localhost:3000**
2. You'll land on the **Documents** page
3. **Upload a PDF**:
   - Drag & drop a PDF file (salary slip, bank statement, etc.)
   - Or click the upload area to browse files
4. **Wait 5-10 seconds** for AI processing
5. **View extracted data**:
   - Document appears in the list on the right
   - Click **"View Details"** to see all extracted financial information

### Step 2: Find Government Schemes

1. Click **"🎯 Find Schemes"** button (floating at bottom-right)
2. Your **financial profile** loads automatically from uploaded documents
3. **Enter what you need**:
   - "home loan" → Housing schemes
   - "business loan" → Business/MSME schemes
   - "education" → Education loan schemes
   - "pension" → Retirement schemes
4. Click **"Search Schemes"**
5. View **AI-ranked recommendations**:
   - Only schemes with 80%+ relevance
   - Sorted by match percentage
   - Complete eligibility criteria
   - Direct links to apply

### Example Workflow

```
1. Upload salary slip PDF
   ↓
2. AI extracts: Name, Salary (₹80,000), Company, PAN
   ↓
3. Data stored in SQLite + Vector DB
   ↓
4. Search: "home loan"
   ↓
5. System analyzes: Income ₹80k/month = ₹9.6L/year
   ↓
6. Returns: PMAY (95% match) - Eligible for income < ₹18L
   ↓
7. User clicks "Learn More" and applies!
```

---

## 🗃️ Database Schema

### SQLite Tables

#### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR UNIQUE,
    name VARCHAR,
    email VARCHAR,
    created_at DATETIME
);
```

#### Documents Table
```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR,
    filename VARCHAR,
    file_type VARCHAR,
    upload_date DATETIME,
    extracted_text TEXT,
    page_count INTEGER,
    file_size FLOAT,
    verification_status VARCHAR,
    doc_metadata TEXT,
    -- Extracted Financial Data
    person_name VARCHAR,
    bank_account_number VARCHAR,
    pan_card_number VARCHAR,
    tax_payable VARCHAR,
    company_name VARCHAR,
    job_role VARCHAR,
    salary VARCHAR,
    address TEXT,
    phone_number VARCHAR,
    email VARCHAR,
    document_type VARCHAR,
    additional_info TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

#### Scheme Recommendations Table
```sql
CREATE TABLE scheme_recommendations (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR,
    query VARCHAR,
    scheme_name VARCHAR,
    scheme_description TEXT,
    eligibility TEXT,
    benefits TEXT,
    source_url VARCHAR,
    relevance_score FLOAT,
    created_at DATETIME
);
```

### Vector Database Collections

- **Collection per user**: `user_{user_id}_financial_data`
- **Stores**: Vector embeddings of financial profile
- **Enables**: Semantic search and similarity matching

---

## 🎨 Key Features Explained

### 1. AI Document Extraction

**Technology**: Groq API with Llama 3.1 70B model

**Process**:
1. Upload PDF → pdfplumber extracts raw text
2. Text sent to Groq AI with structured prompt
3. AI returns JSON with extracted fields
4. Data validated and stored in SQLite
5. Vector embeddings created and stored in ChromaDB

**Accuracy**: AI understands context and variations:
- "Account No", "A/c Number", "Account Number" → All recognized
- Handles multiple document formats
- Extracts even if fields have different names

### 2. Vector Database Intelligence

**Technology**: ChromaDB with Sentence Transformers

**Benefits**:
- **Fast retrieval**: Instant profile access
- **Semantic search**: Understands meaning, not just keywords
- **User isolation**: Each user has separate collection
- **Persistent**: Data saved across sessions

**Use Cases**:
- Profile aggregation from multiple documents
- Similarity matching for scheme recommendations
- Historical analysis of financial data

### 3. Smart Scheme Matching

**Two-Stage Process**:

**Stage 1: Keyword Filtering**
- Scores schemes based on query match
- Category match: +10 points
- Name match: +5 points
- Description match: +2 points
- Threshold: ≥5 points to proceed

**Stage 2: AI Ranking**
- Groq AI analyzes user profile vs scheme
- Considers income, job, location, eligibility
- Ranks by relevance with 80%+ cutoff
- Only shows truly relevant schemes

---

## 🔧 Configuration

### Groq API Key

**Important**: Set your Groq API key as an environment variable:

**Windows PowerShell**:
```powershell
$env:GROQ_API_KEY="your_actual_groq_api_key_here"
```

**Windows CMD**:
```cmd
set GROQ_API_KEY=your_actual_groq_api_key_here
```

**Linux/macOS**:
```bash
export GROQ_API_KEY="your_actual_groq_api_key_here"
```

**Or create a `.env` file** in the backend directory:
```
GROQ_API_KEY=your_actual_groq_api_key_here
```

**To get a Groq API key**:
1. Visit: https://console.groq.com
2. Sign up for free account
3. Generate API key
4. Set as environment variable before running backend

### Port Configuration

**Backend Port** (default: 8000):
```python
# backend/main.py
uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Frontend Port** (default: 3000):
```javascript
// frontend/vite.config.js
export default defineConfig({
  server: { port: 3000 }
})
```

### API URL in Frontend

```javascript
// frontend/src/pages/DocumentUpload.jsx
const API_URL = 'http://localhost:8000';
```

---

## 🐛 Troubleshooting

### Backend won't start
- **Check Python version**: `python --version` (need 3.8+)
- **Install dependencies**: `pip install -r requirements.txt`
- **Check port**: Make sure port 8000 is not in use

### Frontend won't start
- **Check Node version**: `node --version` (need 16+)
- **Install dependencies**: `npm install`
- **Clear cache**: `npm cache clean --force`

### Upload fails
- **Backend running**: Verify http://localhost:8000 is accessible
- **Check browser console**: Look for CORS errors
- **File size**: Ensure PDF is under 10MB
- **File format**: Only PDF files supported

### No schemes found
- **Try different queries**: "loan", "business", "education"
- **Check backend logs**: See which schemes were filtered
- **Upload documents first**: System needs profile data

---

## 🚀 Future Enhancements

### Phase 2 (Planned)
- [ ] Real-time web scraping from government websites
- [ ] Image forensics for document verification
- [ ] Multi-language support (Hindi, regional languages)
- [ ] User authentication & authorization
- [ ] Application tracking system
- [ ] Email notifications for new schemes

### Phase 3 (Planned)
- [ ] Credit risk scoring with ML models
- [ ] Loan affordability calculator with EMI
- [ ] Scheme comparison tool
- [ ] Mobile app (React Native)
- [ ] Chatbot for scheme queries
- [ ] Document verification with blockchain

---

## 👥 Team

**Project**: Credit Sense - AI-Powered Financial Assessment Platform

**Team Members**:
- **Sham Kedar** - 2324000511
- **Sanket Khatkale** - 2324000693
- **Pranav Kapratwar** - 2324000556 (Branch: `pranav-dev`)
- **Nishkarsh Hallikhede** - 2324000822

**Guide**: Mr. Shubham Sontale

**Institution**: KIT's College of Engineering, Kolhapur  
**Department**: Computer Science & Engineering (AIML)  
**Academic Year**: 2023-2024

---

## 📄 License

This project is for **academic purposes** only.

---

## 🙏 Acknowledgments

- **Groq AI** for providing fast LLM inference
- **ChromaDB** for vector database capabilities
- **Government of India** for scheme information
- **KIT Kolhapur** for project guidance
- **Open Source Community** for amazing tools

---

## 📞 Support

For questions or issues:
1. Check [Troubleshooting](#troubleshooting) section
2. Review API documentation at http://localhost:8000/docs
3. Contact team members

---

## 🎉 Quick Start Summary

```bash
# 1. Clone & checkout branch
git clone https://github.com/Sanket-378/Credit-Sense.git
cd Credit-Sense
git checkout pranav-dev

# 2. Setup backend
cd backend
pip install -r requirements.txt

# 3. Setup frontend
cd ../frontend
npm install

# 4. Run backend (Terminal 1)
cd ../backend
python main.py

# 5. Run frontend (Terminal 2)
cd frontend
npm run dev

# 6. Open browser
# http://localhost:3000
```

**That's it! Your AI-powered financial platform is ready! 🚀**

---

**Made with ❤️ by Team Credit Sense**
