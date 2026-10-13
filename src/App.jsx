import { Suspense, lazy, useEffect } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import Footer from './components/Footer.jsx'
import LoadingState from './components/LoadingState.jsx'

const Welcome = lazy(() => import('./pages/Welcome.jsx'))
const Documents = lazy(() => import('./pages/Documents.jsx'))
const FinancialHealth = lazy(() => import('./pages/FinancialHealth.jsx'))
const CreditRisk = lazy(() => import('./pages/CreditRisk.jsx'))
const Affordability = lazy(() => import('./pages/Affordability.jsx'))
const Schemes = lazy(() => import('./pages/Schemes.jsx'))
const NotFound = lazy(() => import('./pages/NotFound.jsx'))

function ScrollToTop() {
  const { pathname } = useLocation()

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [pathname])

  return null
}

export default function App() {
  return (
    <div className="min-h-screen">
      <ScrollToTop />
      <Navbar />
      <main className="min-h-[calc(100vh-160px)]">
        <Suspense fallback={<LoadingState />}>
          <Routes>
            <Route path="/" element={<Welcome />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/financial-health" element={<FinancialHealth />} />
            <Route path="/credit-risk" element={<CreditRisk />} />
            <Route path="/affordability" element={<Affordability />} />
            <Route path="/schemes" element={<Schemes />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </main>
      <Footer />
    </div>
  )
}
