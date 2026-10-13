import { Link } from 'react-router-dom'
import { ArrowUpRight, Calculator, ChartNoAxesCombined, FileCheck2, Gauge, Landmark } from 'lucide-react'

const icons = { FileCheck2, ChartNoAxesCombined, Gauge, Calculator, Landmark }

export default function FeatureCard({ feature, to, compact = false }) {
  const Icon = icons[feature.icon] || FileCheck2
  const content = (
    <>
      <div className={`feature-icon feature-icon-${feature.color || 'blue'}`}>
        <Icon size={21} strokeWidth={1.8} aria-hidden="true" />
      </div>
      <h3 className="feature-title">{feature.title}</h3>
      <p className="feature-description">{feature.description}</p>
      {to && <span className="feature-arrow" aria-hidden="true"><ArrowUpRight size={16} /></span>}
      {!compact && <span className="feature-index">{feature.index}</span>}
    </>
  )

  return to
    ? <Link to={to} className="feature-card feature-card-link">{content}</Link>
    : <article className="feature-card">{content}</article>
}
