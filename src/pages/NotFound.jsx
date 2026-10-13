import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'

export default function NotFound() {
  return (
    <section className="not-found page-shell">
      <span>404</span>
      <h1>This page took a wrong turn.</h1>
      <p>Let’s get you back to your financial picture.</p>
      <Link to="/" className="button button-primary"><ArrowLeft size={16} /> Back to home</Link>
    </section>
  )
}
