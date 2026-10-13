import { createContext, useCallback, useContext, useState } from 'react'

const STORAGE_KEY = 'creditsense.verification'
const VerificationContext = createContext(null)

function readStoredVerification() {
  try {
    const stored = window.sessionStorage.getItem(STORAGE_KEY)
    if (!stored) return null
    const parsed = JSON.parse(stored)
    if (typeof parsed.profile_id !== 'string' || !parsed.overall || !Array.isArray(parsed.documents)) {
      window.sessionStorage.removeItem(STORAGE_KEY)
      return null
    }
    return parsed
  } catch {
    console.warn('Stored verification data could not be restored.')
    try {
      window.sessionStorage.removeItem(STORAGE_KEY)
    } catch (error) {
      console.error('Invalid verification data could not be removed from this browser session.', error)
    }
    return null
  }
}

export function VerificationProvider({ children }) {
  const [verification, setVerification] = useState(readStoredVerification)

  const saveVerification = useCallback((result) => {
    setVerification(result)
    try {
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(result))
    } catch (error) {
      console.error('Verification results could not be saved to this browser session.', error)
    }
  }, [])

  const clearVerification = useCallback(() => {
    setVerification(null)
    try {
      window.sessionStorage.removeItem(STORAGE_KEY)
    } catch (error) {
      console.error('Verification results could not be removed from this browser session.', error)
    }
  }, [])

  return (
    <VerificationContext.Provider
      value={{ verification, profileId: verification?.profile_id ?? null, saveVerification, clearVerification }}
    >
      {children}
    </VerificationContext.Provider>
  )
}

export function useVerification() {
  const context = useContext(VerificationContext)
  if (!context) throw new Error('useVerification must be used within VerificationProvider.')
  return context
}
