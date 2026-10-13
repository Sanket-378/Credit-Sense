import { ArrowRight, Lightbulb } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import PageHeader from '../components/PageHeader.jsx'
import StatCard from '../components/StatCard.jsx'
import { useVerification } from '../context/VerificationContext.jsx'
import { analyzeFinancialHealth } from '../services/financialAnalysis.js'

const compactCurrency = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  notation: 'compact',
  maximumFractionDigits: 1,
})
const formatCompact = (value) => compactCurrency.format(value)
const formatCurrency = (value) => `₹${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

function EmptyChart({ children }) {
  return <div className="empty-state"><h3>Not enough statement data yet</h3><p>{children}</p><Link to="/documents" className="text-button">Upload a statement</Link></div>
}

export default function FinancialHealth() {
  const { verification } = useVerification()
  const data = analyzeFinancialHealth(verification)

  return (
    <div className="page-shell">
      <PageHeader
        eyebrow="YOUR MONEY, MADE CLEAR"
        title="Financial health"
        description="A transaction-based summary of the documents you verified. Missing information is shown as unavailable rather than estimated."
      />
      {!data ? (
        <section className="panel empty-state">
          <h2>Start with your documents</h2>
          <p>Verify a salary slip, bank statement, or UPI statement to see figures and insights based on your extracted data.</p>
          <Link to="/documents" className="button button-primary">Review your documents <ArrowRight size={16} /></Link>
        </section>
      ) : (
        <>
          {data.statementSource && (
            <p className="page-description" aria-live="polite">
              Statement analysis uses <strong>{data.statementSource}</strong> and its latest six observed transaction months.
              Other statements are not combined, to avoid double-counting overlapping transactions.
            </p>
          )}
          <div className="stats-grid">{data.stats.map((stat) => <StatCard key={stat.label} stat={stat} />)}</div>
          <div className="chart-grid">
            <section className="panel chart-panel">
              <div className="panel-heading"><div><h2>Statement credits vs. debits</h2><p>Monthly transaction totals from the selected statement</p></div><span className="chart-legend"><i className="legend-income" /> Credits <i className="legend-expenses" /> Debits</span></div>
              {data.monthly.length ? (
                <div className="chart-area bar-chart-area"><ResponsiveContainer width="100%" height="100%"><BarChart data={data.monthly} barGap={8}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#edf0f6" /><XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: '#8993a5', fontSize: 12 }} dy={10} /><YAxis tickFormatter={formatCompact} tickLine={false} axisLine={false} tick={{ fill: '#8993a5', fontSize: 11 }} width={48} /><Tooltip formatter={(value) => [formatCurrency(value), '']} contentStyle={{ borderRadius: 12, border: '1px solid #edf0f6', boxShadow: '0 8px 28px #172b4d12' }} /><Bar dataKey="income" name="Credits" fill="#315be8" radius={[5, 5, 0, 0]} maxBarSize={20} /><Bar dataKey="expenses" name="Debits" fill="#a6b8f7" radius={[5, 5, 0, 0]} maxBarSize={20} /></BarChart></ResponsiveContainer></div>
              ) : <EmptyChart>Upload a bank or UPI statement containing dated transactions.</EmptyChart>}
            </section>
            <section className="panel chart-panel breakdown-panel">
              <div className="panel-heading"><div><h2>Estimated debit categories</h2><p>Categories inferred from transaction descriptions</p></div></div>
              {data.expenses.length ? (
                <div className="pie-content">
                  <div className="chart-area pie-chart-area"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={data.expenses} dataKey="value" nameKey="name" innerRadius={58} outerRadius={82} paddingAngle={3} stroke="none">{data.expenses.map((item) => <Cell key={item.name} fill={item.color} />)}</Pie><Tooltip formatter={(value) => [`${value}%`, 'Share']} /></PieChart></ResponsiveContainer><div className="pie-center"><strong>{formatCompact(data.stats.find((stat) => stat.label === 'Statement debits')?.value || 0)}</strong><span>observed debits</span></div></div>
                  <div className="pie-legend">{data.expenses.map((item) => <div key={item.name}><span><i style={{ backgroundColor: item.color }} />{item.name}</span><strong>{item.value}%</strong></div>)}</div>
                </div>
              ) : <EmptyChart>Debit categories will appear when the statement includes readable debit descriptions.</EmptyChart>}
            </section>
            <section className="panel chart-panel cash-flow-panel">
              <div className="panel-heading"><div><h2>Net statement cash flow</h2><p>Recorded credits minus recorded debits</p></div></div>
              {data.cashFlow.length ? (
                <div className="chart-area line-chart-area"><ResponsiveContainer width="100%" height="100%"><LineChart data={data.cashFlow}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#edf0f6" /><XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: '#8993a5', fontSize: 12 }} dy={10} /><YAxis tickFormatter={formatCompact} tickLine={false} axisLine={false} tick={{ fill: '#8993a5', fontSize: 11 }} width={48} /><Tooltip formatter={(value) => [formatCurrency(value), 'Net cash flow']} contentStyle={{ borderRadius: 12, border: '1px solid #edf0f6' }} /><Line type="monotone" dataKey="amount" stroke="#16b8a6" strokeWidth={3} dot={{ fill: '#fff', stroke: '#16b8a6', strokeWidth: 2, r: 4 }} activeDot={{ r: 6 }} /></LineChart></ResponsiveContainer></div>
              ) : <EmptyChart>Upload a bank or UPI statement containing dated transactions.</EmptyChart>}
            </section>
            <section className="panel insight-panel">
              <div className="insight-heading"><span><Lightbulb size={18} /></span><div><h2>What the documents show</h2><p>Simple observations from extracted figures</p></div></div>
              <ul>{data.insights.map((insight, index) => <li key={insight}><span>{String(index + 1).padStart(2, '0')}</span>{insight}</li>)}</ul>
              <p className="insight-disclaimer">Credits may include transfers or refunds, not just income. Spending categories are estimates based on descriptions. This is not financial advice.</p>
            </section>
          </div>
        </>
      )}
    </div>
  )
}
