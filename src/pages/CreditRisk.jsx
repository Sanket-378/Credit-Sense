import { useEffect, useState } from 'react'
import { ArrowDownRight, ArrowUpRight, CheckCircle2, CircleHelp, Sparkles } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import PageHeader from '../components/PageHeader.jsx'
import ScoreGauge from '../components/ScoreGauge.jsx'
import LoadingState from '../components/LoadingState.jsx'
import { getCreditScore } from '../services/api.js'

export default function CreditRisk() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getCreditScore().then(setData).catch((requestError) => {
      setError('We could not load your credit assessment right now.')
      console.error('Credit score request failed:', requestError)
    })
  }, [])

  if (error) return <div className="page-shell"><PageHeader eyebrow="UNDERSTAND YOUR SCORE" title="Credit risk assessment" /><p className="error-message" role="alert">{error}</p></div>
  if (!data) return <div className="page-shell"><PageHeader eyebrow="UNDERSTAND YOUR SCORE" title="Credit risk assessment" /><LoadingState /></div>

  return (
    <div className="page-shell">
      <PageHeader eyebrow="UNDERSTAND YOUR SCORE" title="Credit risk assessment" description="Your score is a starting point — understanding what shapes it is where progress begins." />
      <section className="score-overview panel">
        <div className="score-gauge-wrap"><ScoreGauge score={data.score} maxScore={data.maxScore} risk={data.risk} /></div>
        <div className="score-overview-copy">
          <span className="eyebrow">YOUR CREDIT PROFILE</span>
          <h2>You're building a <span>stronger story.</span></h2>
          <p>Your profile shows several encouraging habits. A few steady changes could help strengthen your score over time.</p>
          <div className="risk-label risk-medium"><span /> {data.risk} risk profile <CircleHelp size={15} aria-label="A general estimate based on your current financial profile" /></div>
          <div className="score-range"><span>Needs work</span><div><i /><i /><i className="range-active" /><i /><i /></div><span>Excellent</span></div>
        </div>
        <div className="score-stat"><span>Score range</span><strong>{data.maxScore}</strong><small>out of 900</small><div className="score-change"><ArrowUpRight size={15} /> +24 pts <span>this year</span></div></div>
      </section>

      <div className="risk-content-grid">
        <section className="panel factor-panel">
          <div className="panel-heading"><div><h2>What shapes your score</h2><p>Every factor is shown, so you know what matters.</p></div><span className="explainable-badge"><Sparkles size={14} /> Explainable AI</span></div>
          <div className="factor-chart-wrap"><ResponsiveContainer width="100%" height={240}><BarChart data={data.factors} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 4 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#edf0f6" /><XAxis type="number" domain={[-25, 40]} tickLine={false} axisLine={false} tick={{ fill: '#8993a5', fontSize: 11 }} /><YAxis type="category" dataKey="name" width={135} tickLine={false} axisLine={false} tick={{ fill: '#667085', fontSize: 11 }} /><Tooltip formatter={(value) => [`${value > 0 ? '+' : ''}${value} pts`, 'Contribution']} contentStyle={{ borderRadius: 12, border: '1px solid #edf0f6' }} /><Bar dataKey="contribution" name="Score impact" radius={[0, 4, 4, 0]} maxBarSize={18}>{data.factors.map((factor) => <Cell key={factor.name} fill={factor.contribution >= 0 ? '#16b8a6' : '#f08a7a'} />)}</Bar></BarChart></ResponsiveContainer></div>
          <div className="factor-list">{data.factors.map((factor) => <div className="factor-row" key={factor.name}><span className={`factor-indicator ${factor.contribution >= 0 ? 'factor-positive' : 'factor-negative'}`}>{factor.contribution >= 0 ? <ArrowUpRight size={15} /> : <ArrowDownRight size={15} />}</span><div><strong>{factor.name}</strong><p>{factor.description}</p></div><span className={`factor-score ${factor.contribution >= 0 ? 'positive-text' : 'negative-text'}`}>{factor.contribution > 0 ? '+' : ''}{factor.contribution}</span></div>)}</div>
        </section>
        <aside className="panel improve-panel">
          <div className="improve-head"><span><Sparkles size={18} /></span><div><h2>Ways to improve</h2><p>Small habits, meaningful momentum</p></div></div>
          <ol>{data.improvements.map((item, index) => <li key={item}><span>{index + 1}</span><p>{item}</p></li>)}</ol>
          <div className="improve-note"><CheckCircle2 size={16} /> Changes take time to show up — consistency matters.</div>
        </aside>
      </div>
    </div>
  )
}
