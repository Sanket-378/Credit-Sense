import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'

export function BackButton({ to = '/', children = 'Back' }) {
  return (
    <Link to={to} className="back-link">
      <ArrowLeft size={16} aria-hidden="true" />
      {children}
    </Link>
  )
}

export default function PageHeader({ eyebrow, title, description, backTo = '/' }) {
  return (
    <div className="mb-8">
      <BackButton to={backTo} />
      <div className="mt-6">
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1 className="page-title">{title}</h1>
        {description && <p className="page-description">{description}</p>}
      </div>
    </div>
  )
}
