import { affordabilityProfile, creditRisk, features, financialHealth, schemes } from '../data/mockData.js'

const MOCK_DELAY = 650
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001'
const DOCUMENT_TYPE_IDS = {
  'Salary Slip': 'salary_slip',
  'Bank Statement': 'bank_statement',
  'UPI / Wallet Statement': 'upi_statement',
  Invoice: 'invoice',
  'ID Proof': 'id_proof',
}

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

export async function verifyDocuments(files) {
  const formData = new FormData()
  files.forEach(({ file, type }) => {
    const docType = DOCUMENT_TYPE_IDS[type]
    if (!docType) throw new Error(`Unsupported document type: ${type}`)
    formData.append('files', file, file.name)
    formData.append('doc_types', docType)
  })

  let response
  try {
    response = await fetch(`${API_URL.replace(/\/$/, '')}/api/documents/verify`, {
      method: 'POST',
      body: formData,
    })
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error('We couldn’t reach the verification service. Please check that the CreditSense backend is running and try again.')
    }
    throw error
  }

  let payload
  try {
    payload = await response.json()
  } catch {
    throw new Error('The verification service returned an unreadable response. Please try again.')
  }
  if (!response.ok) {
    const message = typeof payload.detail === 'string'
      ? payload.detail
      : 'We couldn’t verify your documents. Please check the files and try again.'
    throw new Error(message)
  }
  return payload
}
