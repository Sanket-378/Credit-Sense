export const features = [
  {
    title: 'Document Verification',
    description: 'OCR, multimodal AI and image forensics verify salary slips, bank statements and invoices.',
    icon: 'FileCheck2',
    color: 'blue',
  },
  {
    title: 'Financial Health Analysis',
    description: 'Extracted salary and statement data show cash flow and estimated spending patterns.',
    icon: 'ChartNoAxesCombined',
    color: 'teal',
  },
  {
    title: 'Credit Risk Assessment',
    description: 'ML with Explainable AI predicts risk and explains the factors behind it.',
    icon: 'Gauge',
    color: 'violet',
  },
  {
    title: 'Loan Affordability',
    description: 'EMI and repayment capacity checks to prevent over-borrowing.',
    icon: 'Calculator',
    color: 'amber',
  },
  {
    title: 'Government Scheme Discovery',
    description: "RAG, web sources and AI agents match relevant schemes to your profile.",
    icon: 'Landmark',
    color: 'rose',
  },
]

export const affordabilityProfile = {
  monthlyIncome: 78500,
}

export const creditRisk = {
  score: 685,
  maxScore: 900,
  risk: 'Medium',
  factors: [
    { name: 'Payment consistency', score: 82, contribution: 34, description: 'Most payments have been on time over the last year.' },
    { name: 'Debt-to-income ratio', score: 54, contribution: -18, description: 'Your current debt uses a moderate share of monthly income.' },
    { name: 'Income stability', score: 76, contribution: 24, description: 'Regular monthly deposits show a fairly stable income pattern.' },
    { name: 'Document verification', score: 91, contribution: 28, description: 'Submitted financial documents passed authenticity checks.' },
    { name: 'Credit history length', score: 48, contribution: -12, description: 'A shorter credit history gives lenders less repayment history to review.' },
  ],
  improvements: [
    'Pay every bill and EMI on or before its due date.',
    'Try to keep credit card balances below 30% of their limits.',
    'Avoid applying for several new credit accounts at once.',
    'Keep building a consistent record with your existing accounts.',
  ],
}

export const schemes = [
  {
    name: 'PM Mudra Yojana',
    category: ['Business', 'Individual'],
    description: 'Collateral-free loans to help micro and small businesses start or grow.',
    eligibility: 'Non-farm micro businesses and small entrepreneurs.',
    benefits: 'Loans up to ₹10 lakh across Shishu, Kishor and Tarun categories.',
    match: 96,
    tag: 'Micro business',
  },
  {
    name: 'Stand-Up India',
    category: ['Business', 'Women', 'Startup'],
    description: 'Bank loans that support greenfield businesses led by women and SC/ST entrepreneurs.',
    eligibility: 'SC/ST or women entrepreneurs setting up a new enterprise.',
    benefits: 'Composite loans from ₹10 lakh to ₹1 crore.',
    match: 88,
    tag: 'Entrepreneurship',
  },
  {
    name: 'PMEGP',
    category: ['Business', 'Startup'],
    description: 'Credit-linked subsidy programme for setting up new micro-enterprises.',
    eligibility: 'Individuals over 18 and eligible groups establishing a new unit.',
    benefits: 'Margin money subsidy that varies by category and location.',
    match: 83,
    tag: 'Business launch',
  },
  {
    name: 'CGTMSE',
    category: ['Business', 'Startup'],
    description: 'Credit guarantee support that helps micro and small businesses access loans.',
    eligibility: 'New and existing micro and small enterprises with eligible credit.',
    benefits: 'Guarantee cover for eligible collateral-free institutional credit.',
    match: 79,
    tag: 'Credit support',
  },
  {
    name: 'PM SVANidhi',
    category: ['Business', 'Individual'],
    description: 'Working-capital support designed for street vendors.',
    eligibility: 'Street vendors with a certificate of vending or letter of recommendation.',
    benefits: 'Progressive working-capital loans with incentives for timely repayment.',
    match: 72,
    tag: 'Working capital',
  },
  {
    name: 'Atal Pension Yojana',
    category: ['Individual'],
    description: 'A voluntary pension scheme that helps build retirement income over time.',
    eligibility: 'Indian citizens aged 18–40 with a savings bank account.',
    benefits: 'Guaranteed minimum monthly pension after age 60, subject to contribution.',
    match: 68,
    tag: 'Retirement',
  },
]
