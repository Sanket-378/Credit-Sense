const MONTH_FORMATTER = new Intl.DateTimeFormat('en-IN', {
  month: 'short',
  year: '2-digit',
  timeZone: 'UTC',
})
const CURRENCY_FORMATTER = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})
const EXPENSE_CATEGORIES = [
  { name: 'Housing', color: '#315be8', pattern: /\b(rent|mortgage|housing|maintenance|society)\b/i },
  { name: 'Essentials', color: '#16b8a6', pattern: /\b(grocery|groceries|supermarket|pharmacy|medicine|hospital|electricity|water|gas|internet|mobile recharge)\b/i },
  { name: 'Transport', color: '#f1a84b', pattern: /\b(uber|ola|taxi|cab|fuel|petrol|diesel|metro|bus|train|toll|parking)\b/i },
  { name: 'Dining', color: '#9b83eb', pattern: /\b(restaurant|cafe|coffee|swiggy|zomato|food delivery|dining)\b/i },
  { name: 'Shopping', color: '#f08a7a', pattern: /\b(amazon|flipkart|shopping|retail|clothing|apparel)\b/i },
  { name: 'Debt payments', color: '#50728f', pattern: /\b(loan|emi|credit card payment|card payment)\b/i },
  { name: 'Other', color: '#cbd5e1', pattern: /.*/ },
]

function numericAmount(value) {
  if (typeof value === 'boolean' || value === null || value === undefined || value === '') return null
  const amount = typeof value === 'number'
    ? value
    : Number(String(value).replace(/[₹,\s]/g, ''))
  return Number.isFinite(amount) ? Math.abs(amount) : null
}

function parseDate(value) {
  if (typeof value !== 'string') return null
  const isoDate = /^(\d{4})-(\d{2})-(\d{2})/.exec(value)
  const slashDate = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(value)
  if (!isoDate && !slashDate) return null
  const year = Number(isoDate ? isoDate[1] : slashDate[3])
  const month = Number(isoDate ? isoDate[2] : slashDate[2])
  const day = Number(isoDate ? isoDate[3] : slashDate[1])
  const date = new Date(Date.UTC(year, month - 1, day))
  if (
    date.getUTCFullYear() !== year
    || date.getUTCMonth() !== month - 1
    || date.getUTCDate() !== day
  ) return null
  return date
}

function categorizeExpense(description) {
  return EXPENSE_CATEGORIES.find(({ pattern }) => pattern.test(description || '')) || EXPENSE_CATEGORIES.at(-1)
}

function statementRows(documents) {
  const candidates = documents
    .filter((document) => ['bank_statement', 'upi_statement'].includes(document?.doc_type))
    .map((document) => {
      const transactions = Array.isArray(document.extracted_data?.transactions)
        ? document.extracted_data.transactions
        : []
      const rows = transactions.flatMap((transaction) => {
        if (!transaction || typeof transaction !== 'object') return []
        const date = parseDate(transaction.date)
        const debit = numericAmount(transaction.debit)
        const credit = numericAmount(transaction.credit)
        if (!date || (debit === null && credit === null)) return []
        return [{ date, debit: debit || 0, credit: credit || 0, description: transaction.description || '' }]
      })
      return { document, rows }
    })
    .filter(({ rows }) => rows.length)
    .sort((left, right) => (
      right.rows.length - left.rows.length
      || Number(right.document.doc_type === 'bank_statement') - Number(left.document.doc_type === 'bank_statement')
    ))
  return candidates[0] || null
}

function formatMonth(date) {
  return MONTH_FORMATTER.format(date)
}

function formatCurrency(value) {
  return CURRENCY_FORMATTER.format(value)
}

export function analyzeFinancialHealth(verification) {
  const documents = Array.isArray(verification?.documents) ? verification.documents : []
  const salaryDocument = [...documents].reverse().find((document) => (
    document?.doc_type === 'salary_slip'
    && numericAmount(document.extracted_data?.net_salary) !== null
  ))
  const salary = salaryDocument
    ? numericAmount(salaryDocument.extracted_data.net_salary)
    : null
  const selectedStatement = statementRows(documents)
  const transactionMonths = new Map()
  const expenseTotalsByMonth = new Map()

  for (const row of selectedStatement?.rows || []) {
    const monthKey = `${row.date.getUTCFullYear()}-${String(row.date.getUTCMonth() + 1).padStart(2, '0')}`
    const month = transactionMonths.get(monthKey) || {
      date: new Date(Date.UTC(row.date.getUTCFullYear(), row.date.getUTCMonth(), 1)),
      income: 0,
      expenses: 0,
      transactionCount: 0,
    }
    month.income += row.credit
    month.expenses += row.debit
    month.transactionCount += 1
    transactionMonths.set(monthKey, month)

    if (row.debit > 0) {
      const category = categorizeExpense(row.description)
      const monthExpenseTotals = expenseTotalsByMonth.get(monthKey) || new Map()
      monthExpenseTotals.set(category.name, (monthExpenseTotals.get(category.name) || 0) + row.debit)
      expenseTotalsByMonth.set(monthKey, monthExpenseTotals)
    }
  }

  const visibleMonths = [...transactionMonths.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .slice(-6)
  const monthly = visibleMonths
    .map(([, month]) => ({ ...month, month: formatMonth(month.date) }))
  const observedDebits = monthly.reduce((total, month) => total + month.expenses, 0)
  const observedCredits = monthly.reduce((total, month) => total + month.income, 0)
  const netCashFlow = observedCredits - observedDebits
  const observedTransactionCount = monthly.reduce((total, month) => total + month.transactionCount, 0)
  const expenseTotals = new Map()
  for (const [monthKey] of visibleMonths) {
    for (const [category, amount] of expenseTotalsByMonth.get(monthKey) || []) {
      expenseTotals.set(category, (expenseTotals.get(category) || 0) + amount)
    }
  }
  const categorizedExpenses = [...expenseTotals.entries()]
    .map(([name, value]) => ({
      name,
      value: observedDebits ? Math.round((value / observedDebits) * 100) : 0,
      color: EXPENSE_CATEGORIES.find((category) => category.name === name)?.color || '#cbd5e1',
      amount: value,
    }))
    .sort((left, right) => right.amount - left.amount)
  const expenses = categorizedExpenses.filter((item) => item.value > 0)
  const statementSource = selectedStatement?.document.filename || null
  const statementMonths = monthly.length
  const cashFlow = monthly.map((month) => ({
    month: month.month,
    amount: month.income - month.expenses,
  }))
  const stats = [
    {
      label: 'Net salary',
      value: salary,
      change: salaryDocument
        ? `Salary slip${salaryDocument.extracted_data.month ? ` · ${salaryDocument.extracted_data.month}` : ''}`
        : 'Not found in uploaded documents',
      icon: 'TrendingUp',
      tone: 'teal',
    },
    {
      label: 'Statement credits',
      value: selectedStatement ? observedCredits : null,
      change: selectedStatement ? `Across ${statementMonths} observed month${statementMonths === 1 ? '' : 's'}` : 'Upload a bank or UPI statement',
      icon: 'Wallet',
      tone: 'blue',
    },
    {
      label: 'Statement debits',
      value: selectedStatement ? observedDebits : null,
      change: selectedStatement ? `Across ${statementMonths} observed month${statementMonths === 1 ? '' : 's'}` : 'Upload a bank or UPI statement',
      icon: 'CreditCard',
      tone: 'violet',
    },
    {
      label: 'Net statement cash flow',
      value: selectedStatement ? netCashFlow : null,
      change: selectedStatement ? 'Credits minus debits observed' : 'Not enough transaction data',
      icon: 'PiggyBank',
      tone: 'amber',
    },
  ]

  if (!salaryDocument && !selectedStatement) return null

  const insights = []
  if (monthly.length) {
    const positiveMonths = monthly.filter((month) => month.income > month.expenses).length
    insights.push(
      `Statement credits exceeded debits in ${positiveMonths} of ${monthly.length} observed month${monthly.length === 1 ? '' : 's'}.`,
    )
    const topExpense = categorizedExpenses.find((item) => item.name !== 'Other')
    if (topExpense) {
      insights.push(
        `${topExpense.name} is the largest identified debit category at ${topExpense.value}% of recorded debits. Categories are estimated from transaction descriptions.`,
      )
    }
    insights.push(
      `This summary uses ${observedTransactionCount} dated transaction${observedTransactionCount === 1 ? '' : 's'} from ${statementSource}.`,
    )
  } else {
    insights.push('Upload a bank or UPI statement with dated transactions to see cash flow and spending patterns.')
  }
  if (salary !== null) {
    insights.push(`Net salary extracted from your salary slip: ${formatCurrency(salary)}${salaryDocument.extracted_data.month ? ` for ${salaryDocument.extracted_data.month}` : ''}.`)
  }

  return {
    stats,
    monthly,
    expenses,
    cashFlow,
    insights,
    statementSource,
    statementMonths,
  }
}
