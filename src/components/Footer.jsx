import { Link } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <Link to="/" className="brand footer-brand">
          <span className="brand-mark">c</span>
          <span>credit<span className="brand-light">sense</span></span>
        </Link>
        <p className="privacy-note"><ShieldCheck size={15} aria-hidden="true" /> Your information stays yours. Documents are securely deleted after processing.</p>
        <span className="footer-copy">© 2025 CreditSense</span>
      </div>
    </footer>
  )
}
