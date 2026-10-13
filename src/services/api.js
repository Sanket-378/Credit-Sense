import { affordabilityProfile, creditRisk, features, schemes } from '../data/mockData.js'

const MOCK_DELAY = 650
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001'
const USER_ID_STORAGE_KEY = 'creditsense.userId'
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
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

export function getCreditScore() {
  return mockRequest(creditRisk)
}

export function getSchemes() {
  return mockRequest(schemes)
}

function getUserId() {
  const storedUserId = window.localStorage.getItem(USER_ID_STORAGE_KEY)
  if (storedUserId && UUID_PATTERN.test(storedUserId)) return storedUserId

  if (!window.crypto?.randomUUID) {
    throw new Error('This browser cannot create a secure verification ID. Please use an up-to-date browser.')
  }
  const userId = window.crypto.randomUUID()
  window.localStorage.setItem(USER_ID_STORAGE_KEY, userId)
  return userId
}

export async function verifyDocuments(files) {
  const userId = getUserId()
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
      headers: { 'X-User-ID': userId },
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
