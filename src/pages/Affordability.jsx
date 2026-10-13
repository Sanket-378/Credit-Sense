import { useEffect, useMemo, useState } from 'react'
import { ArrowRight, BadgeCheck, Calculator, CircleHelp, ShieldCheck, Wallet } from 'lucide-react'
import { Link } from 'react-router-dom'
import PageHeader from '../components/PageHeader.jsx'
import LoadingState from '../components/LoadingState.jsx'
import { getAffordabilityProfile } from '../services/api.js'

const currency = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
const numberFormat = new Intl.NumberFormat('en-IN')

function calculateEmi(principal, annualRate, months) {
  const monthlyRate = annualRate / 12 / 100
  if (monthlyRate === 0) return principal / months
  const factor = (1 + monthlyRate) ** months
  return (principal * monthlyRate * factor) / (factor - 1)
}

function NumberField({ label, value, onChange, min, max, step, suffix, prefix }) {
  return (
    <label className="calculator-field">
      <span>{label}</span>
      <div className="number-input-wrap">
        {prefix && <span className="input-affix">{prefix}</span>}
        <input type="number" min={min} max={max} step={step} value={value} onChange={(event) => onChange(Math.min(max, Math.max(min, Number(event.target.value) || min)))} />
        {suffix && <span className="input-affix">{suffix}</span>}
      </div>
    </label>
  )
}

function CalculatorSlider({ label, value, min, max, step, onChange, display, prefix, suffix }) {
  return (
    <div className="slider-control">
      <div className="slider-top"><label>{label}</label><strong>{prefix}{display}{suffix}</strong></div>
      <input aria-label={label} type="range" min={min} max={max} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} style={{ '--slider-progress': `${((value - min) / (max - min)) * 100}%` }} />
      <div className="slider-range"><span>{prefix}{prefix === '₹' ? numberFormat.format(min) : min}{suffix}</span><span>{prefix}{prefix === '₹' ? numberFormat.format(max) : max}{suffix}</span></div>
    </div>
  )
}

export default function Affordability() {
  const [amount, setAmount] = useState(800000)
  const [rate, setRate] = useState(10.5)
  const [years, setYears] = useState(5)
  const [monthlyIncome, setMonthlyIncome] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getAffordabilityProfile()
      .then((profile) => setMonthlyIncome(profile.monthlyIncome))
      .catch((requestError) => {
        setError('We could not load your income estimate right now.')
        console.error('Affordability profile request failed:', requestError)
      })
  }, [])

  const results = useMemo(() => {
    if (!monthlyIncome) return null
    const emi = calculateEmi(amount, rate, years * 12)
    const totalPayable = emi * years * 12
    const totalInterest = totalPayable - amount
    const debtToIncome = (emi / monthlyIncome) * 100
    const capacity = debtToIncome <= 30 ? 'Safe' : debtToIncome <= 45 ? 'Caution' : 'Risky'
    const recommendedAmount = Math.round((monthlyIncome * 0.3) / calculateEmi(1, rate, years * 12) / 10000) * 10000
    return { emi, totalPayable, totalInterest, debtToIncome, capacity, recommendedAmount }
  }, [amount, rate, years])

  if (error) return <div className="page-shell"><PageHeader eyebrow="PLAN BEFORE YOU BORROW" title="Loan affordability" /><p className="error-message" role="alert">{error}</p></div>
  if (!results) return <div className="page-shell"><PageHeader eyebrow="PLAN BEFORE YOU BORROW" title="Loan affordability" description="Explore a monthly repayment that feels comfortable, not just possible." /><LoadingState label="Loading your affordability estimate…" /></div>
  const capacityTone = results.capacity.toLowerCase()

  return (
    <div className="page-shell">
      <PageHeader eyebrow="PLAN BEFORE YOU BORROW" title="Loan affordability" description="Explore a monthly repayment that feels comfortable, not just possible." />
      <div className="income-banner"><span><Wallet size={18} /></span><p>Based on your monthly income of <strong>{currency.format(monthlyIncome)}</strong></p><button type="button" aria-label="Income estimate information"><CircleHelp size={16} /></button></div>
      <div className="calculator-layout">
        <section className="panel calculator-panel">
          <div className="panel-heading"><div><h2>Shape your loan</h2><p>Adjust the numbers to see what works for you.</p></div><span className="calculator-heading-icon"><Calculator size={19} /></span></div>
          <div className="slider-controls">
            <CalculatorSlider label="Loan amount" value={amount} min={50000} max={5000000} step={50000} onChange={setAmount} prefix="₹" display={numberFormat.format(amount)} />
            <CalculatorSlider label="Interest rate" value={rate} min={5} max={24} step={0.1} onChange={setRate} display={rate.toFixed(1)} suffix="%" />
            <CalculatorSlider label="Loan tenure" value={years} min={1} max={30} step={1} onChange={setYears} display={years} suffix={years === 1 ? ' year' : ' years'} />
          </div>
          <div className="manual-inputs">
            <NumberField label="Loan amount" prefix="₹" value={amount} min={50000} max={5000000} step={50000} onChange={setAmount} />
            <NumberField label="Interest rate" value={rate} min={5} max={24} step={0.1} suffix="%" onChange={setRate} />
            <NumberField label="Tenure" value={years} min={1} max={30} step={1} suffix={years === 1 ? 'year' : 'years'} onChange={setYears} />
          </div>
          <p className="calculator-footnote"><ShieldCheck size={15} /> Estimates are for guidance only; actual loan terms may vary.</p>
        </section>
        <aside className="panel result-panel">
          <div className="result-heading"><div><span className="eyebrow">YOUR ESTIMATE</span><h2>Monthly EMI</h2></div><span className="result-emoji"><Calculator size={19} /></span></div>
          <strong className="emi-amount">{currency.format(Math.round(results.emi))}<small>/ month</small></strong>
          <div className="result-divider" />
          <div className="result-line"><span>Total interest</span><strong>{currency.format(Math.round(results.totalInterest))}</strong></div>
          <div className="result-line"><span>Total payable</span><strong>{currency.format(Math.round(results.totalPayable))}</strong></div>
          <div className={`capacity-card capacity-${capacityTone}`}>
            <div className="capacity-top"><span className="capacity-icon"><BadgeCheck size={18} /></span><div><strong>{results.capacity} repayment range</strong><small>{results.debtToIncome.toFixed(1)}% of your monthly income</small></div></div>
            <div className="capacity-track"><span style={{ width: `${Math.min(results.debtToIncome, 100)}%` }} /></div>
            <div className="capacity-scale"><span>0%</span><span>30% recommended</span><span>100%</span></div>
          </div>
          <div className="recommended-loan"><span>Recommended safe loan amount</span><strong>{currency.format(results.recommendedAmount)}</strong><small>Based on a 30% EMI-to-income guideline</small></div>
          <Link className="button button-primary result-cta" to="/documents">Explore your profile <ArrowRight size={16} /></Link>
        </aside>
      </div>
    </div>
  )
}
