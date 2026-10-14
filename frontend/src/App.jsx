import React, { useState } from 'react';
import DocumentUpload from './pages/DocumentUpload';
import SchemeRecommendations from './pages/SchemeRecommendations';

function App() {
  const [currentPage, setCurrentPage] = useState('documents');

  return (
    <div className="App">
      {/* Navigation */}
      <div style={{ position: 'fixed', bottom: '2rem', right: '2rem', zIndex: 1000, display: 'flex', gap: '0.5rem' }}>
        <button
          onClick={() => setCurrentPage('documents')}
          style={{
            padding: '0.75rem 1.5rem',
            background: currentPage === 'documents' ? 'linear-gradient(135deg, #059669 0%, #10b981 100%)' : 'white',
            color: currentPage === 'documents' ? 'white' : '#059669',
            border: '2px solid #059669',
            borderRadius: '9999px',
            fontSize: '0.875rem',
            fontWeight: '600',
            cursor: 'pointer',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            transition: 'all 0.2s'
          }}
        >
          📄 Documents
        </button>
        <button
          onClick={() => setCurrentPage('schemes')}
          style={{
            padding: '0.75rem 1.5rem',
            background: currentPage === 'schemes' ? 'linear-gradient(135deg, #059669 0%, #10b981 100%)' : 'white',
            color: currentPage === 'schemes' ? 'white' : '#059669',
            border: '2px solid #059669',
            borderRadius: '9999px',
            fontSize: '0.875rem',
            fontWeight: '600',
            cursor: 'pointer',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            transition: 'all 0.2s'
          }}
        >
          🎯 Find Schemes
        </button>
      </div>

      {/* Page Content */}
      {currentPage === 'documents' ? <DocumentUpload /> : <SchemeRecommendations />}
    </div>
  );
}

export default App;
