import { CreditCard, PiggyBank, TrendingUp, Wallet } from 'lucide-react'

const icons = { TrendingUp, Wallet, CreditCard, PiggyBank }
const currency = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })

export default function StatCard({ stat }) {
  const Icon = icons[stat.icon] || Wallet
  const formattedValue = stat.value === null || stat.value === undefined
    ? '—'
    : stat.suffix
      ? `${stat.value}${stat.suffix}`
      : currency.format(stat.value)

  return (
    <article className="stat-card">
      <div className={`stat-icon stat-icon-${stat.tone}`}><Icon size={19} aria-hidden="true" /></div>
      <p className="stat-label">{stat.label}</p>
      <div className="stat-value-row">
        <strong className="stat-value">{formattedValue}</strong>
        <span className="stat-change">{stat.change}</span>
      </div>
    </article>
  )
}
