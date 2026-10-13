import { affordabilityProfile, creditRisk, features, financialHealth, schemes, verificationResult } from '../data/mockData.js'

const MOCK_DELAY = 650

function mockRequest(data, delay = MOCK_DELAY) {
  return new Promise((resolve) => {
    window.setTimeout(() => resolve(data), delay)
  })
}

export function getFeatures() {
  return mockRequest(features)
}

export function getAffordabilityProfile() {
  return mockRequest(affordabilityProfile)
}

export function getFinancialHealth() {
  return mockRequest(financialHealth)
}

export function getCreditScore() {
  return mockRequest(creditRisk)
}

export function getSchemes() {
  return mockRequest(schemes)
}

export function getVerificationResult() {
  return mockRequest(verificationResult, 1800)
}
