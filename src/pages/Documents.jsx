import { useEffect, useState } from 'react'
import { ArrowRight, Check, CheckCircle2, FileCheck2, LockKeyhole, ScanSearch, ShieldCheck } from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import UploadBox from '../components/UploadBox.jsx'
import FeatureCard from '../components/FeatureCard.jsx'
import LoadingState from '../components/LoadingState.jsx'
import { getFeatures, getVerificationResult } from '../services/api.js'

const nextSteps = [
  { title: 'Financial Health', description: 'Understand your income, expenses and savings.', icon: 'ChartNoAxesCombined', color: 'teal', to: '/financial-health' },
  { title: 'Credit Risk', description: 'See your score and the factors that shape it.', icon: 'Gauge', color: 'violet', to: '/credit-risk' },
  { title: 'Loan Affordability', description: 'Explore repayments that fit your budget.', icon: 'Calculator', color: 'amber', to: '/affordability' },
  { title: 'Government Schemes', description: 'Find support matched to your situation.', icon: 'Landmark', color: 'rose', to: '/schemes' },
]

export default function Documents() {
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [features, setFeatures] = useState([])
  const [featuresError, setFeaturesError] = useState('')

  useEffect(() => {
    getFeatures().then(setFeatures).catch((requestError) => {
      setFeaturesError('We could not load the next steps right now.')
      console.error('Feature list request failed:', requestError)
    })
  }, [])

  async function verifyDocuments(event) {
    event.preventDefault()
    setError('')
    setLoading(true)
    setResult(null)
    try {
      const verification = await getVerificationResult()
      setResult(verification)
    } catch (requestError) {
      setError('We could not verify your documents right now. Please try again.')
      console.error('Document verification failed:', requestError)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-shell">
      <PageHeader eyebrow="STEP 01 · YOUR DOCUMENTS" title="Upload your documents" description="A few documents help us build a more complete, accurate picture of your finances." />
      <div className="step-track" aria-label="Step 1 of 5: Documents"><div className="step-track-top"><span>Get your financial picture</span><span>1 of 5</span></div><div className="step-progress"><span /></div></div>
      <form onSubmit={verifyDocuments} className="document-layout">
        <div>
          <UploadBox files={files} onFilesChange={setFiles} disabled={loading} />
          <div className="verification-assurance"><LockKeyhole size={15} /> Your documents are encrypted, only used to create your analysis, and securely deleted after processing.</div>
          {error && <p className="error-message" role="alert">{error}</p>}
          {loading && <div className="result-wrap"><LoadingState label="Reviewing your documents securely…" /></div>}
          {result && !loading && (
            <section className="verification-result panel" aria-live="polite">
              <div className="verification-result-head"><span className="success-icon"><CheckCircle2 size={21} /></span><div><h2>Verification complete</h2><p>Your documents are ready for analysis.</p></div></div>
              <div className="verification-metrics">
                <div><span>Authenticity score</span><strong className="authenticity-score">{result.authenticity}<small>/100</small></strong></div>
                <div><span>OCR extraction</span><strong><Check size={16} /> {result.ocrStatus}</strong></div>
                <div><span>Forgery check</span><strong><ShieldCheck size={16} /> {result.forgeryStatus}</strong></div>
              </div>
            </section>
          )}
          <button type="submit" className="button button-primary verify-button" disabled={!files.length || loading}>
            {loading ? <><span className="button-spinner" /> Verifying documents</> : <>Verify Documents <ArrowRight size={17} /></>}
          </button>
        </div>
        <aside className="document-side-note">
          <span className="side-note-icon"><ScanSearch size={20} /></span>
          <h2>What happens next?</h2>
          <p>We check that your documents are genuine and securely extract the details needed for your assessment.</p>
          <ul><li><CheckCircle2 size={16} /> Secure document checks</li><li><CheckCircle2 size={16} /> Clear, explainable results</li><li><CheckCircle2 size={16} /> You stay in control</li></ul>
          <div className="side-note-divider" />
          <p className="side-note-small"><FileCheck2 size={15} /> A recent salary slip or bank statement works best.</p>
        </aside>
      </form>

      <section className="next-steps-section">
        <div className="next-steps-heading"><div><p className="eyebrow">Explore your finances</p><h2>Your next steps</h2></div><span>All tools are available to explore</span></div>
        {featuresError ? <p className="error-message" role="alert">{featuresError}</p> : <div className="next-steps-grid">
          {nextSteps.map((item) => {
            const feature = features.find((entry) => entry.title === item.title) || item
            return <FeatureCard key={item.title} feature={{ ...feature, ...item }} to={item.to} compact />
          })}
        </div>}
      </section>
    </div>
  )
}
