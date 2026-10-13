import assert from 'node:assert/strict'
import test from 'node:test'
import { analyzeFinancialHealth } from './financialAnalysis.js'

test('returns no analysis before documents are verified', () => {
  assert.equal(analyzeFinancialHealth(null), null)
  assert.equal(analyzeFinancialHealth({ documents: [] }), null)
})

test('summarizes extracted salary and the latest six observed statement months', () => {
  const transactions = [
    { date: '2024-12-15', description: 'Rent', debit: 10000 },
    { date: '2025-01-12', description: 'Rent', debit: 1000 },
    { date: '2025-02-02', description: 'Salary', credit: 2000 },
    { date: '2025-02-03', description: 'Rent payment', debit: 1000 },
    { date: '2025-03-05', description: 'Grocery supermarket', debit: 500 },
    { date: 'not-a-date', description: 'Ignored', credit: 9000 },
  ]
  for (let month = 4; month <= 7; month += 1) {
    transactions.push({
      date: `2025-${String(month).padStart(2, '0')}-15`,
      description: 'Card payment',
      debit: 100,
    })
  }
  const analysis = analyzeFinancialHealth({
    documents: [
      { doc_type: 'salary_slip', extracted_data: { net_salary: 50000, month: 'July 2025' } },
      { doc_type: 'bank_statement', filename: 'statement.pdf', extracted_data: { transactions } },
    ],
  })

  assert.equal(analysis.statementSource, 'statement.pdf')
  assert.equal(analysis.monthly.length, 6)
  assert.deepEqual(analysis.monthly.map(({ month }) => month), ['Feb 25', 'Mar 25', 'Apr 25', 'May 25', 'Jun 25', 'Jul 25'])
  assert.equal(analysis.stats.find(({ label }) => label === 'Net salary').value, 50000)
  assert.equal(analysis.stats.find(({ label }) => label === 'Statement credits').value, 2000)
  assert.equal(analysis.stats.find(({ label }) => label === 'Statement debits').value, 1900)
  assert.equal(analysis.stats.find(({ label }) => label === 'Net statement cash flow').value, 100)
  assert.deepEqual(analysis.expenses.map(({ name, value }) => [name, value]), [['Housing', 53], ['Essentials', 26], ['Debt payments', 21]])
  assert.ok(analysis.insights.some((insight) => insight.includes('7 dated transactions')))
})

test('keeps statement metrics unavailable when only a salary slip is present', () => {
  const analysis = analyzeFinancialHealth({
    documents: [{ doc_type: 'salary_slip', extracted_data: { net_salary: 45000 } }],
  })

  assert.equal(analysis.monthly.length, 0)
  assert.equal(analysis.stats.find(({ label }) => label === 'Statement credits').value, null)
  assert.equal(analysis.stats.find(({ label }) => label === 'Statement debits').value, null)
})
