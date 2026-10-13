import { useEffect, useState } from 'react'
import { Lightbulb, TrendingUp } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import PageHeader from '../components/PageHeader.jsx'
import StatCard from '../components/StatCard.jsx'
import LoadingState from '../components/LoadingState.jsx'
import { getFinancialHealth } from '../services/api.js'

const formatCompact = (value) => `₹${Math.round(value / 1000)}k`

export default function FinancialHealth() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getFinancialHealth().then(setData).catch((requestError) => {
      setError('We could not load your financial health right now.')
      console.error('Financial health request failed:', requestError)
    })
  }, [])

  if (error) return <div className="page-shell"><PageHeader eyebrow="YOUR MONEY, MADE CLEAR" title="Financial health" /><p className="error-message" role="alert">{error}</p></div>
  if (!data) return <div className="page-shell"><PageHeader eyebrow="YOUR MONEY, MADE CLEAR" title="Financial health" /><LoadingState /></div>
  const monthlyExpenses = data.stats.find((stat) => stat.label === 'Monthly expenses')?.value ?? 0

  return (
    <div className="page-shell">
      <PageHeader eyebrow="YOUR MONEY, MADE CLEAR" title="Financial health" description="A clearer view of what comes in, what goes out, and how you're building ahead." />
      <div className="stats-grid">{data.stats.map((stat) => <StatCard key={stat.label} stat={stat} />)}</div>
      <div className="chart-grid">
        <section className="panel chart-panel">
          <div className="panel-heading"><div><h2>Income vs. expenses</h2><p>Your monthly money in and out</p></div><span className="chart-legend"><i className="legend-income" /> Income <i className="legend-expenses" /> Expenses</span></div>
          <div className="chart-area bar-chart-area"><ResponsiveContainer width="100%" height="100%"><BarChart data={data.monthly} barGap={8}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#edf0f6" /><XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: '#8993a5', fontSize: 12 }} dy={10} /><YAxis tickFormatter={formatCompact} tickLine={false} axisLine={false} tick={{ fill: '#8993a5', fontSize: 11 }} width={48} /><Tooltip formatter={(value) => [`₹${Number(value).toLocaleString('en-IN')}`, '']} contentStyle={{ borderRadius: 12, border: '1px solid #edf0f6', boxShadow: '0 8px 28px #172b4d12' }} /><Bar dataKey="income" name="Income" fill="#315be8" radius={[5, 5, 0, 0]} maxBarSize={20} /><Bar dataKey="expenses" name="Expenses" fill="#a6b8f7" radius={[5, 5, 0, 0]} maxBarSize={20} /></BarChart></ResponsiveContainer></div>
        </section>
        <section className="panel chart-panel breakdown-panel">
          <div className="panel-heading"><div><h2>Expense breakdown</h2><p>Where your money goes</p></div></div>
          <div className="pie-content">
            <div className="chart-area pie-chart-area"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={data.expenses} dataKey="value" nameKey="name" innerRadius={58} outerRadius={82} paddingAngle={3} stroke="none">{data.expenses.map((item) => <Cell key={item.name} fill={item.color} />)}</Pie><Tooltip formatter={(value) => [`${value}%`, 'Share']} /></PieChart></ResponsiveContainer><div className="pie-center"><strong>{formatCompact(monthlyExpenses)}</strong><span>this month</span></div></div>
            <div className="pie-legend">{data.expenses.map((item) => <div key={item.name}><span><i style={{ backgroundColor: item.color }} />{item.name}</span><strong>{item.value}%</strong></div>)}</div>
          </div>
        </section>
        <section className="panel chart-panel cash-flow-panel">
          <div className="panel-heading"><div><h2>Cash flow</h2><p>Monthly income left after expenses</p></div><span className="positive-pill"><TrendingUp size={14} /> Trending up</span></div>
          <div className="chart-area line-chart-area"><ResponsiveContainer width="100%" height="100%"><LineChart data={data.cashFlow}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#edf0f6" /><XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: '#8993a5', fontSize: 12 }} dy={10} /><YAxis tickFormatter={formatCompact} tickLine={false} axisLine={false} tick={{ fill: '#8993a5', fontSize: 11 }} width={48} /><Tooltip formatter={(value) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Cash flow']} contentStyle={{ borderRadius: 12, border: '1px solid #edf0f6' }} /><Line type="monotone" dataKey="amount" stroke="#16b8a6" strokeWidth={3} dot={{ fill: '#fff', stroke: '#16b8a6', strokeWidth: 2, r: 4 }} activeDot={{ r: 6 }} /></LineChart></ResponsiveContainer></div>
        </section>
        <section className="panel insight-panel">
          <div className="insight-heading"><span><Lightbulb size={18} /></span><div><h2>Your AI insights</h2><p>Little things that add up</p></div></div>
          <ul>{data.insights.map((insight, index) => <li key={insight}><span>{String(index + 1).padStart(2, '0')}</span>{insight}</li>)}</ul>
          <p className="insight-disclaimer">A helpful guide, not financial advice.</p>
        </section>
      </div>
    </div>
  )
}
