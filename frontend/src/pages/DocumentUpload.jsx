import React, { useState, useEffect } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Trash2, Eye, X } from 'lucide-react';

export default function DocumentUpload() {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const API_URL = 'http://localhost:8000';

  // Fetch documents on mount
  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${API_URL}/api/documents`);
      if (response.ok) {
        const data = await response.json();
        setUploadedFiles(data);
      }
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const handleFileUpload = async (files) => {
    if (!files || files.length === 0) return;

    setUploading(true);
    const file = files[0];

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_URL}/api/upload-document`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        alert(`✅ Document uploaded successfully!\n\nFilename: ${data.filename}\nPages: ${data.page_count}\nStatus: ${data.verification_status}`);
        fetchDocuments();
      } else {
        const error = await response.json();
        alert(`❌ Upload failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('❌ Upload failed. Make sure the backend server is running on http://localhost:8000');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
      const response = await fetch(`${API_URL}/api/documents/${id}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        alert('✅ Document deleted successfully!');
        fetchDocuments();
      }
    } catch (error) {
      console.error('Delete error:', error);
      alert('❌ Failed to delete document');
    }
  };

  const handleViewDetails = async (id) => {
    try {
      const response = await fetch(`${API_URL}/api/documents/${id}`);
      if (response.ok) {
        const data = await response.json();
        setSelectedFile(data);
      }
    } catch (error) {
      console.error('Error fetching document details:', error);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50" style={{
      background: 'linear-gradient(135deg, #ecfeff 0%, #ffffff 50%, #fef3c7 100%)'
    }}>
      {/* Header */}
      <div className="bg-white shadow-sm" style={{
        background: 'linear-gradient(90deg, #0891b2 0%, #059669 100%)',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
      }}>
        <div className="max-w-7xl mx-auto px-4 py-6" style={{ padding: '1.5rem 1rem' }}>
          <div className="flex items-center gap-3" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{
              background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(245, 158, 11, 0.3)'
            }}>
              <FileText style={{ width: '24px', height: '24px', color: 'white' }} />
            </div>
            <div>
              <h1 className="text-3xl font-bold" style={{ fontSize: '1.875rem', fontWeight: '700', color: 'white', margin: 0 }}>
                Credit Sense
              </h1>
              <p style={{ fontSize: '0.875rem', color: '#ecfeff', marginTop: '0.25rem' }}>
                AI-Powered Financial Assessment & Credit Guidance Platform
              </p>
            </div>
          </div>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 py-8" style={{ maxWidth: '80rem', margin: '0 auto', padding: '2rem 1rem' }}>
        <div className="mb-8" style={{ marginBottom: '2rem' }}>
          <h2 style={{ 
            fontSize: '1.875rem', 
            fontWeight: '700', 
            background: 'linear-gradient(90deg, #059669 0%, #0891b2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: '0.5rem'
          }}>
            Document Upload & Verification
          </h2>
          <p style={{ color: '#4b5563', fontSize: '1rem' }}>
            Upload your financial documents for AI-powered verification and analysis
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <div>
            <div className="bg-white rounded-2xl shadow-lg p-6" style={{
              background: 'white',
              borderRadius: '1rem',
              padding: '1.5rem',
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.08)',
              border: '1px solid #e5e7eb'
            }}>
              <h3 className="text-xl font-bold mb-4" style={{ 
                fontSize: '1.25rem', 
                fontWeight: '700',
                marginBottom: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                color: '#059669'
              }}>
                <Upload style={{ width: '1.25rem', height: '1.25rem' }} />
                Upload Documents
              </h3>
              
              {/* Drag & Drop Upload Box */}
              <div
                className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all`}
                style={{
                  position: 'relative',
                  border: dragActive ? '3px solid #059669' : '2px dashed #d1d5db',
                  borderRadius: '0.75rem',
                  padding: '2rem',
                  textAlign: 'center',
                  transition: 'all 0.3s ease',
                  background: dragActive ? 'linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)' : '#fafafa',
                  cursor: 'pointer'
                }}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <input
                  type="file"
                  id="file-upload"
                  style={{ display: 'none' }}
                  accept=".pdf"
                  onChange={(e) => handleFileUpload(e.target.files)}
                  disabled={uploading}
                />
                
                <label htmlFor="file-upload" style={{ cursor: 'pointer' }}>
                  <div style={{
                    width: '64px',
                    height: '64px',
                    margin: '0 auto 1rem',
                    background: uploading ? '#e5e7eb' : 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
                    borderRadius: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 8px 16px rgba(5, 150, 105, 0.2)',
                    animation: uploading ? 'bounce 1s infinite' : 'none'
                  }}>
                    <Upload style={{ width: '32px', height: '32px', color: 'white' }} />
                  </div>
                  <p style={{ fontSize: '1.125rem', fontWeight: '600', color: '#111827', marginBottom: '0.5rem' }}>
                    {uploading ? 'Uploading and Processing...' : 'Drop your PDF here or click to browse'}
                  </p>
                  <p style={{ fontSize: '0.875rem', color: '#6b7280' }}>PDF files only, max 10MB</p>
                </label>

                {uploading && (
                  <div style={{ marginTop: '1rem' }}>
                    <div style={{ 
                      width: '100%', 
                      height: '8px', 
                      background: '#e5e7eb', 
                      borderRadius: '9999px',
                      overflow: 'hidden'
                    }}>
                      <div style={{ 
                        width: '70%', 
                        height: '100%', 
                        background: 'linear-gradient(90deg, #059669 0%, #10b981 100%)',
                        borderRadius: '9999px',
                        animation: 'pulse 2s infinite'
                      }}></div>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="mt-6 p-4 rounded-lg" style={{
                marginTop: '1.5rem',
                padding: '1rem',
                background: 'linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)',
                borderRadius: '0.75rem',
                border: '1px solid #a7f3d0'
              }}>
                <h4 style={{ fontWeight: '600', color: '#047857', marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                  ✓ Accepted Documents:
                </h4>
                <ul style={{ fontSize: '0.875rem', color: '#065f46', margin: 0, paddingLeft: '1.25rem' }}>
                  <li style={{ marginBottom: '0.25rem' }}>Bank Statements (PDF)</li>
                  <li style={{ marginBottom: '0.25rem' }}>Salary Slips</li>
                  <li style={{ marginBottom: '0.25rem' }}>Tax Returns</li>
                  <li style={{ marginBottom: '0.25rem' }}>Business Financial Reports</li>
                  <li>Income Certificates</li>
                </ul>
              </div>

              <div className="mt-4 p-4 rounded-lg" style={{
                marginTop: '1rem',
                padding: '1rem',
                background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
                borderRadius: '0.75rem',
                border: '1px solid #fcd34d'
              }}>
                <h4 style={{ fontWeight: '600', color: '#92400e', marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                  🚀 Features:
                </h4>
                <ul style={{ fontSize: '0.875rem', color: '#78350f', margin: 0, paddingLeft: '1.25rem' }}>
                  <li style={{ marginBottom: '0.25rem' }}>🔍 OCR Text Extraction</li>
                  <li style={{ marginBottom: '0.25rem' }}>✅ Document Verification</li>
                  <li style={{ marginBottom: '0.25rem' }}>📊 Metadata Analysis</li>
                  <li>🔒 Secure Storage</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Uploaded Files List */}
          <div>
            <div className="bg-white rounded-2xl shadow-lg p-6" style={{
              background: 'white',
              borderRadius: '1rem',
              padding: '1.5rem',
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.08)',
              border: '1px solid #e5e7eb'
            }}>
              <h3 style={{ 
                fontSize: '1.25rem', 
                fontWeight: '700',
                marginBottom: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                color: '#0891b2'
              }}>
                <FileText style={{ width: '1.25rem', height: '1.25rem' }} />
                Uploaded Documents ({uploadedFiles.length})
              </h3>
              
              {uploadedFiles.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '3rem 0', color: '#9ca3af' }}>
                  <FileText style={{ width: '4rem', height: '4rem', margin: '0 auto 0.75rem', opacity: 0.3 }} />
                  <p style={{ fontSize: '1.125rem', fontWeight: '500', marginBottom: '0.5rem' }}>No documents uploaded yet</p>
                  <p style={{ fontSize: '0.875rem' }}>Upload your first document to get started</p>
                </div>
              ) : (
                <div style={{ maxHeight: '600px', overflowY: 'auto', paddingRight: '0.5rem' }}>
                  {uploadedFiles.map((file) => (
                    <div key={file.id} style={{
                      padding: '1rem',
                      border: '1px solid #e5e7eb',
                      borderRadius: '0.75rem',
                      marginBottom: '0.75rem',
                      transition: 'all 0.3s ease',
                      cursor: 'pointer'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.boxShadow = '0 4px 12px rgba(5, 150, 105, 0.1)';
                      e.currentTarget.style.borderColor = '#10b981';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.boxShadow = 'none';
                      e.currentTarget.style.borderColor = '#e5e7eb';
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <FileText style={{ width: '1.25rem', height: '1.25rem', color: '#6b7280' }} />
                            <h4 style={{ fontWeight: '600', color: '#111827', margin: 0, wordBreak: 'break-all' }}>{file.filename}</h4>
                          </div>
                          <div style={{ marginTop: '0.5rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                            <span style={{ 
                              background: 'linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 100%)', 
                              padding: '0.25rem 0.5rem', 
                              borderRadius: '0.375rem',
                              fontSize: '0.75rem',
                              color: '#115e59',
                              border: '1px solid #99f6e4'
                            }}>{file.file_size} KB</span>
                            <span style={{ 
                              background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)', 
                              padding: '0.25rem 0.5rem', 
                              borderRadius: '0.375rem',
                              fontSize: '0.75rem',
                              color: '#78350f',
                              border: '1px solid #fcd34d'
                            }}>{file.page_count} pages</span>
                            <span style={{ 
                              background: '#f3f4f6', 
                              padding: '0.25rem 0.5rem', 
                              borderRadius: '0.375rem',
                              fontSize: '0.75rem',
                              color: '#374151'
                            }}>{new Date(file.upload_date).toLocaleDateString()}</span>
                          </div>
                          {file.extracted_text_preview && (
                            <p style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#6b7280', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {file.extracted_text_preview}
                            </p>
                          )}
                        </div>
                        <div style={{ marginLeft: '1rem' }}>
                          {file.verification_status === 'verified' ? (
                            <div style={{ 
                              display: 'flex', 
                              alignItems: 'center', 
                              gap: '0.25rem',
                              background: 'linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)',
                              padding: '0.375rem 0.75rem',
                              borderRadius: '9999px',
                              border: '1px solid #6ee7b7'
                            }}>
                              <CheckCircle style={{ width: '1rem', height: '1rem', color: '#047857' }} />
                              <span style={{ fontSize: '0.75rem', fontWeight: '600', color: '#047857' }}>Verified</span>
                            </div>
                          ) : (
                            <div style={{ 
                              display: 'flex', 
                              alignItems: 'center', 
                              gap: '0.25rem',
                              background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
                              padding: '0.375rem 0.75rem',
                              borderRadius: '9999px',
                              border: '1px solid #fcd34d'
                            }}>
                              <AlertCircle style={{ width: '1rem', height: '1rem', color: '#d97706' }} />
                              <span style={{ fontSize: '0.75rem', fontWeight: '600', color: '#d97706' }}>Review</span>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
                        <button
                          onClick={() => handleViewDetails(file.id)}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                            padding: '0.5rem 0.75rem',
                            fontSize: '0.875rem',
                            background: 'linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)',
                            color: '#047857',
                            border: '1px solid #6ee7b7',
                            borderRadius: '0.5rem',
                            cursor: 'pointer',
                            fontWeight: '500',
                            transition: 'all 0.2s ease'
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = 'linear-gradient(135deg, #059669 0%, #10b981 100%)';
                            e.currentTarget.style.color = 'white';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)';
                            e.currentTarget.style.color = '#047857';
                          }}
                        >
                          <Eye style={{ width: '1rem', height: '1rem' }} />
                          View Details
                        </button>
                        <button
                          onClick={() => handleDelete(file.id)}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                            padding: '0.5rem 0.75rem',
                            fontSize: '0.875rem',
                            background: '#fef2f2',
                            color: '#dc2626',
                            border: '1px solid #fecaca',
                            borderRadius: '0.5rem',
                            cursor: 'pointer',
                            fontWeight: '500',
                            transition: 'all 0.2s ease'
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = '#dc2626';
                            e.currentTarget.style.color = 'white';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = '#fef2f2';
                            e.currentTarget.style.color = '#dc2626';
                          }}
                        >
                          <Trash2 style={{ width: '1rem', height: '1rem' }} />
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Document Details Modal */}
        {selectedFile && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
              <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex justify-between items-start">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">{selectedFile.filename}</h2>
                  <p className="text-sm text-gray-500 mt-1">Document Details</p>
                </div>
                <button
                  onClick={() => setSelectedFile(null)}
                  className="text-gray-400 hover:text-gray-600 transition-colors p-2 hover:bg-gray-100 rounded-lg"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
              
              <div className="p-6">
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="p-4 rounded-lg" style={{
                    background: 'linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)',
                    border: '1px solid #6ee7b7'
                  }}>
                    <p className="text-sm mb-1" style={{ color: '#065f46' }}>File Size</p>
                    <p className="text-xl font-bold" style={{ color: '#047857' }}>{selectedFile.file_size} KB</p>
                  </div>
                  <div className="p-4 rounded-lg" style={{
                    background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
                    border: '1px solid #fcd34d'
                  }}>
                    <p className="text-sm mb-1" style={{ color: '#78350f' }}>Pages</p>
                    <p className="text-xl font-bold" style={{ color: '#92400e' }}>{selectedFile.page_count}</p>
                  </div>
                  <div className="p-4 rounded-lg" style={{
                    background: 'linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)',
                    border: '1px solid #93c5fd'
                  }}>
                    <p className="text-sm mb-1" style={{ color: '#1e3a8a' }}>Status</p>
                    <p className="text-xl font-bold capitalize" style={{ color: '#1e40af' }}>{selectedFile.verification_status}</p>
                  </div>
                  <div className="p-4 rounded-lg" style={{
                    background: 'linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%)',
                    border: '1px solid #d8b4fe'
                  }}>
                    <p className="text-sm mb-1" style={{ color: '#5b21b6' }}>Upload Date</p>
                    <p className="text-sm font-bold" style={{ color: '#6b21a8' }}>{new Date(selectedFile.upload_date).toLocaleString()}</p>
                  </div>
                </div>
                
                {/* Financial Data Section */}
                {selectedFile.financial_data && (
                  <div className="mb-6" style={{
                    background: 'linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)',
                    borderRadius: '0.75rem',
                    padding: '1.5rem',
                    border: '2px solid #059669'
                  }}>
                    <h3 style={{ 
                      fontSize: '1.25rem', 
                      fontWeight: '700', 
                      marginBottom: '1rem',
                      color: '#047857',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem'
                    }}>
                      💰 Extracted Financial Information
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '1rem' }}>
                      {selectedFile.financial_data.document_type && (
                        <div style={{ padding: '0.75rem', background: 'white', borderRadius: '0.5rem', border: '1px solid #a7f3d0' }}>
                          <p style={{ fontSize: '0.75rem', color: '#065f46', marginBottom: '0.25rem' }}>Document Type</p>
                          <p style={{ fontWeight: '600', color: '#047857' }}>{selectedFile.financial_data.document_type}</p>
                        </div>
                      )}
                      {selectedFile.financial_data.person_name && (
                        <div style={{ padding: '0.75rem', background: 'white', borderRadius: '0.5rem', border: '1px solid #a7f3d0' }}>
                          <p style={{ fontSize: '0.75rem', color: '#065f46', marginBottom: '0.25rem' }}>Person Name</p>
                          <p style={{ fontWeight: '600', color: '#047857' }}>{selectedFile.financial_data.person_name}</p>
                        </div>
                      )}
                      {selectedFile.financial_data.company_name && (
                        <div style={{ padding: '0.75rem', background: 'white', borderRadius: '0.5rem', border: '1px solid #a7f3d0' }}>
                          <p style={{ fontSize: '0.75rem', color: '#065f46', marginBottom: '0.25rem' }}>Company Name</p>
                          <p style={{ fontWeight: '600', color: '#047857' }}>{selectedFile.financial_data.company_name}</p>
                        </div>
                      )}
                      {selectedFile.financial_data.job_role && (
                        <div style={{ padding: '0.75rem', background: 'white', borderRadius: '0.5rem', border: '1px solid #a7f3d0' }}>
                          <p style={{ fontSize: '0.75rem', color: '#065f46', marginBottom: '0.25rem' }}>Job Role</p>
                          <p style={{ fontWeight: '600', color: '#047857' }}>{selectedFile.financial_data.job_role}</p>
                        </div>
                      )}
                      {selectedFile.financial_data.salary && (
                        <div style={{ padding: '0.75rem', background: 'white', borderRadius: '0.5rem', border: '1px solid #fcd34d' }}>
                          <p style={{ fontSize: '0.75rem', color: '#78350f', marginBottom: '0.25rem' }}>Salary</p>
                          <p style={{ fontWeight: '600', color: '#92400e' }}>{selectedFile.financial_data.salary}</p>
                        </div>
                      )}
                      {selectedFile.financial_data.bank_account_number && (
                        <div style={{ padding: '0.75rem', background: 'white', borderRadius: '0.5rem', border: '1px solid #fcd34d' }}>
                          <p style={{ fontSize: '0.75rem', color: '#78350f', marginBottom: '0.25rem' }}>Bank Account</p>
                          <p style={{ fontWeight: '600', color: '#92400e' }}>{selectedFile.financial_data.bank_account_number}</p>
                        </div>
                      )}
                      {selectedFile.financial_data.pan_card_number && (
                        <div style={{ padding: '0.75rem', background: 'white', borderRadius: '0.5rem', border: '1px solid #93c5fd' }}>
                          <p style={{ fontSize: '0.75rem', color: '#1e3a8a', marginBottom: '0.25rem' }}>PAN Card Number</p>
                          <p style={{ fontWeight: '600', color: '#1e40af' }}>{selectedFile.financial_data.pan_card_number}</p>
                        </div>
                      )}
                      {selectedFile.financial_data.tax_payable && (
                        <div style={{ padding: '0.75rem', background: 'white', borderRadius: '0.5rem', border: '1px solid #93c5fd' }}>
                          <p style={{ fontSize: '0.75rem', color: '#1e3a8a', marginBottom: '0.25rem' }}>Tax Payable</p>
                          <p style={{ fontWeight: '600', color: '#1e40af' }}>{selectedFile.financial_data.tax_payable}</p>
                        </div>
                      )}
                      {selectedFile.financial_data.email && (
                        <div style={{ padding: '0.75rem', background: 'white', borderRadius: '0.5rem', border: '1px solid #d8b4fe' }}>
                          <p style={{ fontSize: '0.75rem', color: '#5b21b6', marginBottom: '0.25rem' }}>Email</p>
                          <p style={{ fontWeight: '600', color: '#6b21a8', fontSize: '0.875rem' }}>{selectedFile.financial_data.email}</p>
                        </div>
                      )}
                      {selectedFile.financial_data.phone_number && (
                        <div style={{ padding: '0.75rem', background: 'white', borderRadius: '0.5rem', border: '1px solid #d8b4fe' }}>
                          <p style={{ fontSize: '0.75rem', color: '#5b21b6', marginBottom: '0.25rem' }}>Phone Number</p>
                          <p style={{ fontWeight: '600', color: '#6b21a8' }}>{selectedFile.financial_data.phone_number}</p>
                        </div>
                      )}
                      {selectedFile.financial_data.address && (
                        <div style={{ padding: '0.75rem', background: 'white', borderRadius: '0.5rem', border: '1px solid #a7f3d0', gridColumn: 'span 2' }}>
                          <p style={{ fontSize: '0.75rem', color: '#065f46', marginBottom: '0.25rem' }}>Address</p>
                          <p style={{ fontWeight: '600', color: '#047857', fontSize: '0.875rem' }}>{selectedFile.financial_data.address}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                <div className="mb-6">
                  <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">File Size</p>
                    <p className="text-xl font-bold text-gray-900">{selectedFile.file_size} KB</p>
                  </div>
                  <div className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Pages</p>
                    <p className="text-xl font-bold text-gray-900">{selectedFile.page_count}</p>
                  </div>
                  <div className="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Status</p>
                    <p className="text-xl font-bold text-gray-900 capitalize">{selectedFile.verification_status}</p>
                  </div>
                  <div className="p-4 bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Upload Date</p>
                    <p className="text-sm font-bold text-gray-900">{new Date(selectedFile.upload_date).toLocaleString()}</p>
                  </div>
                </div>
                
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-blue-600" />
                    Extracted Text
                  </h3>
                  <div className="p-4 bg-gray-50 rounded-lg max-h-96 overflow-y-auto border border-gray-200">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
                      {selectedFile.extracted_text || 'No text extracted from this document.'}
                    </pre>
                  </div>
                </div>
                
                {selectedFile.metadata && Object.keys(selectedFile.metadata).length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold mb-3">PDF Metadata</h3>
                    <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                      <pre className="text-sm text-gray-700">
                        {JSON.stringify(selectedFile.metadata, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
