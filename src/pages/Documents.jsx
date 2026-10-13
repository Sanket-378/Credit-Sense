import { useEffect, useState } from 'react'
import { ArrowRight, CheckCircle2, FileCheck2, LockKeyhole, ScanSearch, ShieldCheck } from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import UploadBox from '../components/UploadBox.jsx'
import FeatureCard from '../components/FeatureCard.jsx'
import LoadingState from '../components/LoadingState.jsx'
import { getFeatures, verifyDocuments as submitVerification } from '../services/api.js'
import { useVerification } from '../context/VerificationContext.jsx'

const nextSteps = [
  { title: 'Financial Health', description: 'Understand your income, expenses and savings.', icon: 'ChartNoAxesCombined', color: 'teal', to: '/financial-health' },
  { title: 'Credit Risk', description: 'See your score and the factors that shape it.', icon: 'Gauge', color: 'violet', to: '/credit-risk' },
  { title: 'Loan Affordability', description: 'Explore repayments that fit your budget.', icon: 'Calculator', color: 'amber', to: '/affordability' },
  { title: 'Government Schemes', description: 'Find support matched to your situation.', icon: 'Landmark', color: 'rose', to: '/schemes' },
]

const DOCUMENT_TYPE_LABELS = {
  salary_slip: 'Salary Slip',
  bank_statement: 'Bank Statement',
  upi_statement: 'UPI / Wallet Statement',
  invoice: 'Invoice',
  id_proof: 'ID Proof',
}
const MONETARY_FIELDS = new Set([
  'opening_balance',
  'closing_balance',
  'total_credits',
  'total_debits',
])
const currencyFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 2,
})

function numericAmount(value) {
  if (value === null || value === undefined || value === '') return null
  const amount = typeof value === 'number'
    ? value
    : Number(String(value).replace(/[₹,\s]/g, ''))
  return Number.isFinite(amount) ? amount : null
}

function formatCurrency(value) {
  const amount = numericAmount(value)
  return amount === null ? null : currencyFormatter.format(amount)
}

function MissingValue() {
  return <span className="muted-value">Not found</span>
}

function TransactionTable({ transactions, extractedData }) {
  const hasBalance = transactions.some((transaction) => numericAmount(transaction.balance) !== null)
  const debitTotal = transactions.reduce((sum, transaction) => sum + (numericAmount(transaction.debit) || 0), 0)
  const creditTotal = transactions.reduce((sum, transaction) => sum + (numericAmount(transaction.credit) || 0), 0)
  const statedDebit = numericAmount(extractedData.total_debits)
  const statedCredit = numericAmount(extractedData.total_credits)
  const totalsMismatch = (
    (statedDebit !== null && Math.abs(debitTotal - statedDebit) > 1) ||
    (statedCredit !== null && Math.abs(creditTotal - statedCredit) > 1)
  )

  return (
    <section className="transaction-section" aria-label="Extracted transactions">
      <h4>Transactions <span>{transactions.length}</span></h4>
      {transactions.length ? (
        <div className="transaction-table-scroll">
          <table className="transaction-table">
            <thead>
              <tr>
                <th scope="col">Date</th>
                <th scope="col">Description</th>
                <th scope="col">Debit</th>
                <th scope="col">Credit</th>
                {hasBalance && <th scope="col">Balance</th>}
              </tr>
            </thead>
            <tbody>
              {transactions.map((transaction, index) => (
                <tr key={`${transaction.date || 'date'}-${index}`}>
                  <td>{transaction.date || <MissingValue />}</td>
                  <td>{transaction.description || <MissingValue />}</td>
                  <td>{formatCurrency(transaction.debit) || <MissingValue />}</td>
                  <td>{formatCurrency(transaction.credit) || <MissingValue />}</td>
                  {hasBalance && <td>{formatCurrency(transaction.balance) || <MissingValue />}</td>}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : <p className="no-findings">No transactions were found.</p>}
      <div className={`transaction-totals${totalsMismatch ? ' transaction-totals-mismatch' : ''}`} aria-label={totalsMismatch ? 'Transaction totals do not match stated totals' : 'Transaction totals'}>
        <div><strong>Debit total</strong><span>{currencyFormatter.format(debitTotal)}</span><small>Stated: {formatCurrency(extractedData.total_debits) || <MissingValue />}</small></div>
        <div><strong>Credit total</strong><span>{currencyFormatter.format(creditTotal)}</span><small>Stated: {formatCurrency(extractedData.total_credits) || <MissingValue />}</small></div>
      </div>
    </section>
  )
}

function CheckCoverage({ document }) {
  const performed = Array.isArray(document.checks_performed) ? document.checks_performed : []
  const skipped = Array.isArray(document.checks_skipped) ? document.checks_skipped : []

  return (
    <section className="check-coverage" aria-label="Consistency check coverage">
      <h4>Checks performed / skipped</h4>
      {performed.length > 0 && (
        <p><strong>Performed:</strong> {performed.map((name) => name.replaceAll('_', ' ')).join(', ')}</p>
      )}
      {skipped.length > 0 ? (
        <ul>
          {skipped.map(({ name, reason }, index) => (
            <li key={`${name}-${index}`}><strong>{name.replaceAll('_', ' ')} skipped:</strong> {reason}</li>
          ))}
        </ul>
      ) : <p className="coverage-none">No consistency checks were skipped.</p>}
    </section>
  )
}

function CheckSummary({ title, result }) {
  const hasFindings = result.findings.length > 0
  return (
    <details className="document-check" open={hasFindings || undefined}>
      <summary>
        <span>{title}</span>
        <span className={`check-status check-status-${result.status}`}>{result.status.replace('_', ' ')}</span>
      </summary>
      {hasFindings ? (
        <ul className="finding-list">
          {result.findings.map((finding, index) => (
            <li key={`${finding.check}-${index}`}>
              <span className={`finding-severity finding-severity-${finding.severity}`}>{finding.severity}</span>
              <div><strong>{finding.check.replaceAll('_', ' ')}</strong><p>{finding.detail}</p></div>
            </li>
          ))}
        </ul>
      ) : <p className="no-findings">No issues found in this check.</p>}
    </details>
  )
}

function DocumentResultCard({ document }) {
  const extractedData = document.extracted_data || {}
  const transactions = Array.isArray(extractedData.transactions) ? extractedData.transactions : null

  return (
    <article className="document-result-card">
      <div className="document-result-heading">
        <div className="document-result-icon"><FileCheck2 size={18} aria-hidden="true" /></div>
        <div className="document-result-name">
          <h3>{document.filename}</h3>
          <span>{DOCUMENT_TYPE_LABELS[document.doc_type] || document.doc_type.replaceAll('_', ' ')}</span>
        </div>
        <div className="document-result-score">
          <strong>{document.authenticity_score}</strong><span>/100</span>
          <span className={`verdict-badge verdict-${document.verdict}`}>{document.verdict.replaceAll('_', ' ')}</span>
        </div>
      </div>
      <div className="document-result-statuses">
        <div><span>OCR extraction</span><span className={`check-status check-status-${document.ocr_status === 'success' ? 'passed' : document.ocr_status === 'partial' ? 'warning' : 'failed'}`}>{document.ocr_status}</span></div>
        <CheckSummary title="Forgery check" result={document.forgery_check} />
        <CheckSummary title="Consistency check" result={document.consistency_check} />
      </div>
      <CheckCoverage document={document} />
      <details className="extracted-data">
        <summary>Extracted information <span>{document.missing_fields.length ? `${document.missing_fields.length} fields missing` : 'View fields'}</span></summary>
        {Object.keys(extractedData).length ? (
          <dl>
            {Object.entries(extractedData).filter(([key]) => key !== 'transactions').map(([key, value]) => (
              <div key={key}>
                <dt>{key.replaceAll('_', ' ')}</dt>
                <dd className={value === null || value === '' ? 'muted-value' : undefined}>
                  {value === null || value === ''
                    ? 'Not found'
                    : MONETARY_FIELDS.has(key)
                      ? formatCurrency(value) || <MissingValue />
                      : Array.isArray(value)
                        ? `${value.length} items`
                        : typeof value === 'object'
                          ? 'Available'
                          : String(value)}
                </dd>
              </div>
            ))}
          </dl>
        ) : <p className="no-findings">No fields could be extracted from this document.</p>}
        {transactions && <TransactionTable transactions={transactions} extractedData={extractedData} />}
      </details>
    </article>
  )
}

export default function Documents() {
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [features, setFeatures] = useState([])
  const [featuresError, setFeaturesError] = useState('')
  const { verification: result, profileId, saveVerification, clearVerification } = useVerification()

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
    clearVerification()
    try {
      const verification = await submitVerification(files)
      saveVerification(verification)
    } catch (requestError) {
      setError(requestError instanceof Error
        ? requestError.message
        : 'We could not verify your documents right now. Please try again.')
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
          <div className="verification-assurance"><LockKeyhole size={15} /> Your documents are securely deleted after processing. ID numbers are masked before they are saved.</div>
          {error && <p className="error-message" role="alert">{error}</p>}
          {loading && <div className="result-wrap"><LoadingState label="Reviewing your documents securely…" /></div>}
          {result && !loading && (
            <section className="verification-result panel" aria-live="polite">
              <div className="verification-result-head">
                <span className="success-icon"><CheckCircle2 size={21} /></span>
                <div><h2>Verification complete</h2><p>Profile ID: <code>{profileId}</code></p></div>
              </div>
              <div className="overall-result">
                <div><span>Overall authenticity score</span><strong>{result.overall.authenticity_score}<small>/100</small></strong></div>
                <span className={`verdict-badge verdict-${result.overall.verdict}`}>{result.overall.verdict.replaceAll('_', ' ')}</span>
                <span className="processed-count">{result.overall.documents_processed} document{result.overall.documents_processed === 1 ? '' : 's'} processed</span>
              </div>
              <div className="document-results">
                {result.documents.map((document, index) => <DocumentResultCard key={`${document.filename}-${index}`} document={document} />)}
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
