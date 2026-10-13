import { useEffect, useMemo, useState } from 'react'
import { ArrowUpRight, BadgeCheck, Search, Sparkles } from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import LoadingState from '../components/LoadingState.jsx'
import { getSchemes } from '../services/api.js'

const categories = ['All', 'Business', 'Individual', 'Women', 'Startup']

export default function Schemes() {
  const [schemes, setSchemes] = useState(null)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('All')

  useEffect(() => {
    getSchemes().then(setSchemes).catch((requestError) => {
      setError('We could not load schemes right now. Please try again later.')
      console.error('Schemes request failed:', requestError)
    })
  }, [])

  const filteredSchemes = useMemo(() => {
    if (!schemes) return []
    const search = query.trim().toLowerCase()
    return schemes.filter((scheme) => {
      const matchesCategory = category === 'All' || scheme.category.includes(category)
      const matchesSearch = !search || [scheme.name, scheme.description, scheme.eligibility, scheme.benefits, ...scheme.category].join(' ').toLowerCase().includes(search)
      return matchesCategory && matchesSearch
    })
  }, [schemes, query, category])

  return (
    <div className="page-shell">
      <PageHeader eyebrow="SUPPORT THAT FITS YOU" title="Find your next opportunity" description="Explore government programmes that could help you start, grow or plan for what’s next." />
      <div className="scheme-match-banner"><div className="scheme-match-icon"><Sparkles size={19} /></div><div><strong>Matched to your financial profile</strong><p>These programmes are a starting point — check each scheme’s official eligibility details.</p></div><BadgeCheck size={20} className="scheme-match-check" /></div>
      <section className="scheme-explorer">
        <div className="scheme-controls">
          <label className="scheme-search"><Search size={18} aria-hidden="true" /><span className="sr-only">Search schemes</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search schemes, benefits..." /></label>
          <div className="category-filters" role="group" aria-label="Filter schemes by category">
            {categories.map((item) => <button key={item} type="button" className={`filter-chip ${category === item ? 'filter-chip-active' : ''}`} aria-pressed={category === item} onClick={() => setCategory(item)}>{item}</button>)}
          </div>
        </div>
        {error ? <p className="error-message" role="alert">{error}</p> : !schemes ? <LoadingState label="Finding schemes for you…" /> : filteredSchemes.length ? (
          <div className="schemes-grid">{filteredSchemes.map((scheme) => <article className="scheme-card" key={scheme.name}>
            <div className="scheme-card-top"><span className="scheme-tag">{scheme.tag}</span><span className="match-badge"><Sparkles size={12} /> {scheme.match}% match</span></div>
            <h2>{scheme.name}</h2>
            <p className="scheme-description">{scheme.description}</p>
            <div className="scheme-detail"><span>WHO IT’S FOR</span><p>{scheme.eligibility}</p></div>
            <div className="scheme-detail scheme-benefit"><span>HOW IT CAN HELP</span><p>{scheme.benefits}</p></div>
            <div className="scheme-card-bottom"><div className="scheme-categories">{scheme.category.map((item) => <span key={item}>{item}</span>)}</div><a href="https://www.india.gov.in/" target="_blank" rel="noreferrer" className="scheme-link">Learn more <ArrowUpRight size={15} /></a></div>
          </article>)}</div>
        ) : <div className="empty-state"><Search size={22} /><h3>No schemes found</h3><p>Try a different search or choose another category.</p><button type="button" className="text-button" onClick={() => { setQuery(''); setCategory('All') }}>Clear filters</button></div>}
      </section>
      <p className="scheme-disclaimer">Scheme details can change. Please verify current eligibility, terms and application steps with the official programme website.</p>
    </div>
  )
}
