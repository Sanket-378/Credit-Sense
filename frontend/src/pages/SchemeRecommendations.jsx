import React, { useState } from 'react';
import { Search, TrendingUp, CheckCircle, ExternalLink, DollarSign, FileText, User } from 'lucide-react';

export default function SchemeRecommendations() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [schemes, setSchemes] = useState([]);
  const [userProfile, setUserProfile] = useState(null);
  const [activeTab, setActiveTab] = useState('all');

  const API_URL = 'http://localhost:8000';

  const handleSearch = async () => {
    if (!query.trim()) {
      alert('Please enter what you\'re looking for (e.g., home loan, business loan, education)');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/recommend-schemes?query=${encodeURIComponent(query)}&user_id=default_user`, {
        method: 'POST',
      });

      if (response.ok) {
        const data = await response.json();
        setSchemes(data.schemes);
        setUserProfile(data.user_profile);
        setActiveTab('all');
      } else {
        alert('Failed to fetch recommendations');
      }
    } catch (error) {
      console.error('Search error:', error);
      alert('Error: Make sure backend is running');
    } finally {
      setLoading(false);
    }
  };

  const getCategoryColor = (index) => {
    const colors = [
      { bg: 'linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)', border: '#6ee7b7', text: '#047857' },
      { bg: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)', border: '#fcd34d', text: '#92400e' },
      { bg: 'linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)', border: '#93c5fd', text: '#1e40af' },
      { bg: 'linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%)', border: '#d8b4fe', text: '#6b21a8' },
    ];
    return colors[index % colors.length];
  };

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #ecfeff 0%, #ffffff 50%, #fef3c7 100%)' }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(90deg, #0891b2 0%, #059669 100%)',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
      }}>
        <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '1.5rem 1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
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
              <TrendingUp style={{ width: '24px', height: '24px', color: 'white' }} />
            </div>
            <div>
              <h1 style={{ fontSize: '1.875rem', fontWeight: '700', color: 'white', margin: 0 }}>
                Scheme Recommendations
              </h1>
              <p style={{ fontSize: '0.875rem', color: '#ecfeff', marginTop: '0.25rem' }}>
                AI-Powered Government Scheme Finder Based on Your Profile
              </p>
            </div>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '2rem 1rem' }}>
        {/* User Profile Summary */}
        {userProfile && (
          <div style={{
            background: 'linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)',
            borderRadius: '1rem',
            padding: '1.5rem',
            marginBottom: '2rem',
            border: '2px solid #059669'
          }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: '700', color: '#047857', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <User style={{ width: '1.25rem', height: '1.25rem' }} />
              Your Financial Profile
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
              {userProfile.person_name && (
                <div>
                  <p style={{ fontSize: '0.75rem', color: '#065f46' }}>Name</p>
                  <p style={{ fontWeight: '600', color: '#047857' }}>{userProfile.person_name}</p>
                </div>
              )}
              {userProfile.salary && (
                <div>
                  <p style={{ fontSize: '0.75rem', color: '#065f46' }}>Salary</p>
                  <p style={{ fontWeight: '600', color: '#047857' }}>{userProfile.salary}</p>
                </div>
              )}
              {userProfile.company_name && (
                <div>
                  <p style={{ fontSize: '0.75rem', color: '#065f46' }}>Company</p>
                  <p style={{ fontWeight: '600', color: '#047857' }}>{userProfile.company_name}</p>
                </div>
              )}
              {userProfile.job_role && (
                <div>
                  <p style={{ fontSize: '0.75rem', color: '#065f46' }}>Job Role</p>
                  <p style={{ fontWeight: '600', color: '#047857' }}>{userProfile.job_role}</p>
                </div>
              )}
              <div>
                <p style={{ fontSize: '0.75rem', color: '#065f46' }}>Documents Analyzed</p>
                <p style={{ fontWeight: '600', color: '#047857' }}>{userProfile.total_documents}</p>
              </div>
            </div>
          </div>
        )}

        {/* Search Box */}
        <div style={{
          background: 'white',
          borderRadius: '1rem',
          padding: '1.5rem',
          marginBottom: '2rem',
          boxShadow: '0 10px 30px rgba(0, 0, 0, 0.08)',
          border: '1px solid #e5e7eb'
        }}>
          <h2 style={{ 
            fontSize: '1.5rem', 
            fontWeight: '700',
            background: 'linear-gradient(90deg, #059669 0%, #0891b2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: '1rem'
          }}>
            What are you looking for?
          </h2>
          
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <div style={{ flex: 1, position: 'relative' }}>
              <Search style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', width: '1.25rem', height: '1.25rem', color: '#6b7280' }} />
              <input
                type="text"
                placeholder="E.g., home loan, business loan, education, pension, agriculture..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                style={{
                  width: '100%',
                  padding: '0.875rem 1rem 0.875rem 3rem',
                  borderRadius: '0.5rem',
                  border: '2px solid #d1d5db',
                  fontSize: '1rem',
                  outline: 'none',
                  transition: 'all 0.2s'
                }}
                onFocus={(e) => e.target.style.borderColor = '#059669'}
                onBlur={(e) => e.target.style.borderColor = '#d1d5db'}
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={loading}
              style={{
                padding: '0.875rem 2rem',
                background: loading ? '#9ca3af' : 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
                color: 'white',
                border: 'none',
                borderRadius: '0.5rem',
                fontSize: '1rem',
                fontWeight: '600',
                cursor: loading ? 'not-allowed' : 'pointer',
                boxShadow: '0 4px 12px rgba(5, 150, 105, 0.3)',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => !loading && (e.target.style.transform = 'translateY(-2px)')}
              onMouseLeave={(e) => !loading && (e.target.style.transform = 'translateY(0)')}
            >
              {loading ? 'Searching...' : 'Search Schemes'}
            </button>
          </div>

          <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <p style={{ fontSize: '0.875rem', color: '#6b7280' }}>Try:</p>
            {['Home Loan', 'Business Loan', 'Education', 'Pension', 'Agriculture'].map((tag) => (
              <button
                key={tag}
                onClick={() => {setQuery(tag); handleSearch();}}
                style={{
                  padding: '0.25rem 0.75rem',
                  background: '#f3f4f6',
                  border: '1px solid #d1d5db',
                  borderRadius: '9999px',
                  fontSize: '0.875rem',
                  color: '#374151',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.target.style.background = '#e5e7eb';
                  e.target.style.borderColor = '#9ca3af';
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = '#f3f4f6';
                  e.target.style.borderColor = '#d1d5db';
                }}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>

        {/* Results */}
        {schemes.length > 0 && (
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '700', color: '#111827', marginBottom: '1rem' }}>
              🎯 {schemes.length} Scheme{schemes.length > 1 ? 's' : ''} Found Matching "{query}"
            </h3>

            <div style={{ display: 'grid', gap: '1rem' }}>
              {schemes.map((scheme, index) => {
                const color = getCategoryColor(index);
                return (
                  <div
                    key={index}
                    style={{
                      background: color.bg,
                      borderRadius: '0.75rem',
                      padding: '1.5rem',
                      border: `2px solid ${color.border}`,
                      transition: 'all 0.3s'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 8px 24px rgba(0, 0, 0, 0.1)'}
                    onMouseLeave={(e) => e.currentTarget.style.boxShadow = 'none'}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                          <span style={{
                            background: 'white',
                            color: color.text,
                            padding: '0.25rem 0.75rem',
                            borderRadius: '9999px',
                            fontSize: '0.75rem',
                            fontWeight: '700'
                          }}>
                            #{index + 1}
                          </span>
                          <span style={{
                            background: 'white',
                            color: color.text,
                            padding: '0.25rem 0.75rem',
                            borderRadius: '9999px',
                            fontSize: '0.75rem',
                            fontWeight: '600'
                          }}>
                            {Math.round(scheme.relevance_score * 100)}% Match
                          </span>
                        </div>
                        <h4 style={{ fontSize: '1.125rem', fontWeight: '700', color: color.text, marginBottom: '0.5rem' }}>
                          {scheme.name}
                        </h4>
                        <p style={{ fontSize: '0.875rem', color: color.text, opacity: 0.8, marginBottom: '1rem' }}>
                          {scheme.description}
                        </p>
                      </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
                      <div style={{ background: 'white', padding: '1rem', borderRadius: '0.5rem' }}>
                        <p style={{ fontSize: '0.75rem', color: color.text, fontWeight: '600', marginBottom: '0.5rem' }}>
                          ✓ Eligibility
                        </p>
                        <p style={{ fontSize: '0.875rem', color: '#374151' }}>{scheme.eligibility}</p>
                      </div>
                      <div style={{ background: 'white', padding: '1rem', borderRadius: '0.5rem' }}>
                        <p style={{ fontSize: '0.75rem', color: color.text, fontWeight: '600', marginBottom: '0.5rem' }}>
                          💰 Benefits
                        </p>
                        <p style={{ fontSize: '0.875rem', color: '#374151' }}>{scheme.benefits}</p>
                      </div>
                    </div>

                    <a
                      href={scheme.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        padding: '0.5rem 1rem',
                        background: 'white',
                        color: color.text,
                        borderRadius: '0.5rem',
                        fontSize: '0.875rem',
                        fontWeight: '600',
                        textDecoration: 'none',
                        border: `1px solid ${color.border}`,
                        transition: 'all 0.2s'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = color.text;
                        e.currentTarget.style.color = 'white';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'white';
                        e.currentTarget.style.color = color.text;
                      }}
                    >
                      Learn More <ExternalLink style={{ width: '1rem', height: '1rem' }} />
                    </a>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {schemes.length === 0 && !loading && (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>
            <Search style={{ width: '4rem', height: '4rem', margin: '0 auto 1rem', opacity: 0.3 }} />
            <p style={{ fontSize: '1.125rem', fontWeight: '500' }}>
              {query ? `No schemes found for "${query}"` : 'Search for schemes that match your needs'}
            </p>
            <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
              {query 
                ? 'Try a different search term like "loan", "business", "education", or "pension"' 
                : 'Enter what you\'re looking for and we\'ll find the best government schemes for you'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
