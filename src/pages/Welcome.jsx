import { useEffect, useState } from 'react'
import { ArrowRight, ArrowUpRight, Check, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'
import FeatureCard from '../components/FeatureCard.jsx'
import LoadingState from '../components/LoadingState.jsx'
import { getFeatures } from '../services/api.js'

export default function Welcome() {
  const [features, setFeatures] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getFeatures().then(setFeatures).catch((requestError) => {
      setError('We could not load the feature list right now.')
      console.error('Feature list request failed:', requestError)
    })
  }, [])

  return (
    <>
      <section className="hero">
        <div className="hero-grid" aria-hidden="true" />
        <div className="hero-inner">
          <div className="hero-copy">
            <div className="hero-badge"><span className="status-dot" /> A clearer way to move forward</div>
            <h1>Your financial story,<br /><span>finally understood.</span></h1>
            <p>Know where you stand, what you can afford, and what support is out there — all in one simple place.</p>
            <div className="hero-actions">
              <Link to="/documents" className="button button-primary">Generate Score <ArrowRight size={17} aria-hidden="true" /></Link>
              <span className="hero-caption"><Check size={15} aria-hidden="true" /> Free to explore · No impact on credit</span>
            </div>
            <div className="hero-social">
              <div className="avatar-stack" aria-hidden="true"><span>A</span><span>R</span><span>M</span><span>+</span></div>
              <span>Built for real-life finances</span>
            </div>
          </div>
          <div className="hero-art" aria-label="Illustration of financial progress">
            <div className="art-orbit orbit-one" />
            <div className="art-orbit orbit-two" />
            <div className="art-card art-main">
              <div className="art-card-heading"><span>Financial snapshot</span><span className="art-menu">•••</span></div>
              <p className="art-score-label">Your credit score</p>
              <div className="art-score-row"><strong>685</strong><span className="art-trend">↗ 24 pts</span></div>
              <div className="art-progress"><span /></div>
              <div className="art-score-scale"><span>Needs work</span><span>Excellent</span></div>
              <div className="art-mini-chart" aria-hidden="true">
                {[30, 47, 41, 64, 56, 73, 62, 90, 78, 100, 86, 112].map((height, index) => <i key={index} style={{ height: `${height}px` }} />)}
              </div>
              <div className="art-chart-label"><span>Score growth</span><span>Last 12 months</span></div>
            </div>
            <div className="art-float art-float-top"><span className="float-icon"><Sparkles size={15} /></span><div><strong>Looking good</strong><small>Your savings are growing</small></div></div>
            <div className="art-float art-float-bottom"><span className="float-check"><Check size={16} /></span><div><strong>Documents verified</strong><small>3 files · Just now</small></div></div>
            <div className="art-decoration">₹</div>
          </div>
        </div>
        <div className="hero-bottom">
          <span>FINANCIAL CONFIDENCE, BUILT AROUND YOU</span>
          <span><i /> Simple <i /> Supportive <i /> Secure</span>
        </div>
      </section>

      <section className="feature-section section-shell">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Everything in one place</p>
            <h2>Small steps. <span>Big picture.</span></h2>
          </div>
          <p>Practical tools to help you make more confident money decisions — at your own pace.</p>
        </div>
        {error ? <p className="error-message" role="alert">{error}</p> : !features ? <LoadingState label="Loading your tools…" /> : <div className="feature-grid">
          {features.map((feature, index) => (
            <FeatureCard key={feature.title} feature={{ ...feature, index: `0${index + 1}` }} />
          ))}
        </div>}
        <div className="section-cta">
          <div><h3>Ready to see your full picture?</h3><p>It only takes a few minutes to get started.</p></div>
          <Link to="/documents" className="button button-primary">Generate Score <ArrowRight size={17} aria-hidden="true" /></Link>
        </div>
      </section>
      <section className="trust-strip"><div><span className="trust-icon"><Check size={18} /></span><p><strong>Your data stays yours.</strong> We securely delete your uploaded documents after processing.</p><Link to="/documents">Get started <ArrowUpRight size={15} /></Link></div></section>
    </>
  )
}
