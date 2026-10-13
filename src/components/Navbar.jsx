import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { ArrowUpRight, Menu, X } from 'lucide-react'

const links = [
  { to: '/documents', label: 'Get started' },
  { to: '/financial-health', label: 'Financial health' },
  { to: '/credit-risk', label: 'Credit score' },
  { to: '/affordability', label: 'Loan calculator' },
  { to: '/schemes', label: 'Schemes' },
]

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <header className="site-header">
      <nav className="nav-shell" aria-label="Main navigation">
        <Link to="/" className="brand" onClick={() => setMenuOpen(false)} aria-label="CreditSense home">
          <span className="brand-mark">c</span>
          <span>credit<span className="brand-light">sense</span></span>
        </Link>
        <div className={`nav-links ${menuOpen ? 'nav-links-open' : ''}`}>
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              onClick={() => setMenuOpen(false)}
              className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
            >
              {link.label}
            </NavLink>
          ))}
        </div>
        <Link to="/documents" className="nav-cta">
          Start free <ArrowUpRight size={15} aria-hidden="true" />
        </Link>
        <button
          type="button"
          className="menu-toggle"
          aria-label={menuOpen ? 'Close navigation menu' : 'Open navigation menu'}
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((open) => !open)}
        >
          {menuOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </nav>
    </header>
  )
}
