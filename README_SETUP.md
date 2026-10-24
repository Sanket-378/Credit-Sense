# Credit Sense - Document Upload System

AI-Powered Financial Assessment & Credit Guidance Platform with PDF Document Processing

## 🏗️ Architecture

### Backend (FastAPI + Python)
- PDF processing with pdfplumber
- SQLite database for document storage
- REST API endpoints
- Document verification

### Frontend (React + Vite)
- Interactive drag-and-drop file upload
- Real-time document list
- Document details viewer
- Responsive design

## 📋 Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn

## 🚀 Setup Instructions

### Step 1: Install Backend Dependencies

```powershell
cd backend
python -m pip install -r requirements.txt
```

### Step 2: Install Frontend Dependencies

```powershell
cd ../frontend
npm install
```

### Step 3: Start the Backend Server

```powershell
cd ../backend
python main.py
```

The backend will run on: **http://localhost:8000**

API Documentation: **http://localhost:8000/docs**

### Step 4: Start the Frontend Server

Open a new terminal:

```powershell
cd frontend
npm run dev
```

The frontend will run on: **http://localhost:3000**

## 📁 Project Structure

```
Credit-Sense/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── database.py          # SQLite database models
│   ├── requirements.txt     # Python dependencies
│   └── credit_sense.db      # SQLite database (created automatically)
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── DocumentUpload.jsx    # Main upload page
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
└── README_SETUP.md
```

## 🎯 Features

### Document Upload
- ✅ Drag & drop interface
- ✅ File picker option
- ✅ PDF validation
- ✅ Progress indicator

### Document Processing
- 🔍 OCR text extraction with pdfplumber
- 📄 Page count detection
- 📊 File size calculation
- 🔐 Metadata extraction
- ✅ Automatic verification

### Document Management
- 📋 List all uploaded documents
- 👁️ View full document details
- 📝 See extracted text
- 🗑️ Delete documents
- 📊 Verification status

## 🔌 API Endpoints

### GET `/`
Health check

### POST `/api/upload-document`
Upload and process PDF document
- **Input**: PDF file (multipart/form-data)
- **Output**: Document info with extracted text

### GET `/api/documents`
Get all uploaded documents

### GET `/api/documents/{id}`
Get specific document details

### DELETE `/api/documents/{id}`
Delete a document

## 💡 Usage

1. **Start both servers** (backend on port 8000, frontend on port 3000)

2. **Open your browser** to http://localhost:3000

3. **Upload a PDF document** by:
   - Dragging and dropping a PDF file
   - Or clicking to browse and select a file

4. **View the document list** to see:
   - Filename
   - File size
   - Page count
   - Verification status
   - Upload date

5. **Click "View Details"** to see:
   - Extracted text from the PDF
   - Document metadata
   - Full document information

6. **Click "Delete"** to remove a document

## 🛠️ Technologies Used

### Backend
- **FastAPI** - Modern Python web framework
- **pdfplumber** - PDF text extraction
- **SQLAlchemy** - Database ORM
- **SQLite** - Lightweight database
- **Uvicorn** - ASGI server

### Frontend
- **React** - UI library
- **Vite** - Build tool
- **Lucide React** - Icon library
- **Tailwind CSS** - Styling (via CDN)

## 🔧 Configuration

### Change Backend Port
Edit `backend/main.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8000)  # Change port here
```

### Change Frontend Port
Edit `frontend/vite.config.js`:
```javascript
server: {
  port: 3000  // Change port here
}
```

### Change API URL
Edit `frontend/src/pages/DocumentUpload.jsx`:
```javascript
const API_URL = 'http://localhost:8000';  // Change API URL here
```

## 🎨 Features to Add (Future Enhancements)

- [ ] Multiple file upload
- [ ] Image forensics for document verification
- [ ] Financial data extraction from statements
- [ ] Credit risk assessment with ML
- [ ] Government scheme matching
- [ ] User authentication
- [ ] Document categories
- [ ] Search and filter
- [ ] Export functionality

## 📝 Notes

- Only PDF files are supported
- Maximum file size: 10MB (configurable)
- Database is created automatically on first run
- All documents are stored in SQLite database
- CORS is enabled for localhost:3000 and localhost:5173

## 🐛 Troubleshooting

### Backend won't start
- Make sure Python 3.8+ is installed
- Install all requirements: `pip install -r requirements.txt`
- Check if port 8000 is available

### Frontend won't start
- Make sure Node.js 16+ is installed
- Install dependencies: `npm install`
- Check if port 3000 is available

### Upload fails
- Ensure backend is running on http://localhost:8000
- Check browser console for errors
- Verify the file is a valid PDF
- Check file size is under 10MB

### CORS errors
- Make sure both servers are running
- Check that API_URL in frontend matches backend URL
- Verify CORS middleware is configured in backend

## 👥 Team

- Sham Kedar - 2324000511
- Sanket Khatkale - 2324000693
- Pranav Kapratwar - 2324000556
- Nishkarsh Hallikhede - 2324000822

**Guide**: Mr. Shubham Sontale

**Institution**: KIT's College of Engineering Kolhapur

## 📄 License

This project is for academic purposes.
