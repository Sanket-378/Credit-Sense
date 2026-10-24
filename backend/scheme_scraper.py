import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import json
import os
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your_groq_api_key_here")
groq_client = Groq(api_key=GROQ_API_KEY)

# Mock government schemes database (In production, scrape from official websites)
MOCK_SCHEMES = [
    {
        "name": "Pradhan Mantri Awas Yojana (PMAY) - Home Loan Subsidy",
        "description": "Credit Linked Subsidy Scheme for middle and lower income groups to buy or construct houses",
        "eligibility": "Annual household income up to ₹18 lakhs, first-time home buyer, property value within prescribed limits",
        "benefits": "Interest subsidy of up to ₹2.67 lakhs on home loans, reduced EMI burden",
        "category": "home_loan housing real_estate property",
        "source_url": "https://pmaymis.gov.in/"
    },
    {
        "name": "Pradhan Mantri MUDRA Yojana (PMMY)",
        "description": "Loans up to ₹10 lakhs for small businesses and micro enterprises",
        "eligibility": "Small business owners, traders, manufacturers, service providers",
        "benefits": "Collateral-free loans, low interest rates, flexible repayment",
        "category": "business_loan msme entrepreneurship",
        "source_url": "https://www.mudra.org.in/"
    },
    {
        "name": "Stand Up India Scheme",
        "description": "Bank loans between ₹10 lakh to ₹1 crore for SC/ST/Women entrepreneurs",
        "eligibility": "SC/ST/Women aged 18+ years, for greenfield enterprise in manufacturing/services/trading",
        "benefits": "Up to ₹1 crore loan, 7-year repayment period, margin money requirement of 15-25%",
        "category": "business_loan women_entrepreneur startup",
        "source_url": "https://www.standupmitra.in/"
    },
    {
        "name": "PM Kisan Credit Card Scheme",
        "description": "Easy credit facility for farmers to meet agricultural expenses",
        "eligibility": "Farmers with cultivable land, fishermen, dairy farmers",
        "benefits": "Up to ₹3 lakhs credit limit, 2% interest subvention, flexible repayment",
        "category": "agriculture farming credit_card",
        "source_url": "https://pmkisan.gov.in/"
    },
    {
        "name": "Atal Pension Yojana (APY)",
        "description": "Pension scheme for unorganized sector workers",
        "eligibility": "Indian citizens aged 18-40 years with savings bank account",
        "benefits": "Guaranteed minimum pension of ₹1,000 to ₹5,000 per month after 60 years",
        "category": "pension retirement investment savings",
        "source_url": "https://npscra.nsdl.co.in/atal-pension-yojana.php"
    },
    {
        "name": "Pradhan Mantri Rozgar Yojana (PMRY)",
        "description": "Self-employment scheme for educated unemployed youth",
        "eligibility": "Age 18-35 years (40 for SC/ST), family income below ₹40,000/year, 8th standard pass",
        "benefits": "Up to ₹2 lakh loan for business/industry/service sector, subsidy on interest",
        "category": "employment self_employment youth",
        "source_url": "http://www.dcmsme.gov.in/"
    },
    {
        "name": "PM SVANidhi - Street Vendor Loan",
        "description": "Micro-credit facility for street vendors affected by COVID-19",
        "eligibility": "Street vendors selling goods/services, registered/surveyed by ULBs",
        "benefits": "Initial working capital up to ₹10,000, digital payment cashback, interest subsidy",
        "category": "micro_credit street_vendor small_business",
        "source_url": "https://pmsvanidhi.mohua.gov.in/"
    },
    {
        "name": "National Education Loan Scheme",
        "description": "Education loans for higher studies in India and abroad",
        "eligibility": "Indian nationals admitted to recognized institutions, any course approved by government",
        "benefits": "Up to ₹20 lakhs for abroad, ₹10 lakhs for India, interest subsidy during course period",
        "category": "education_loan student higher_education",
        "source_url": "https://www.education.gov.in/"
    },
    {
        "name": "Sukanya Samriddhi Yojana",
        "description": "Small deposit scheme for girl child's education and marriage",
        "eligibility": "Girl child below 10 years, parents/legal guardians can open account",
        "benefits": "High interest rate (7.6%), tax benefits under 80C, maturity amount tax-free",
        "category": "savings girl_child education investment",
        "source_url": "https://www.nsiindia.gov.in/"
    },
    {
        "name": "PM Vishwakarma Scheme",
        "description": "Support for traditional artisans and craftspeople",
        "eligibility": "Artisans working with hands and tools in 18 traditional trades",
        "benefits": "Skill training, toolkit incentive, credit support up to ₹3 lakhs, digital marketing support",
        "category": "artisan craftsman skill_development loan",
        "source_url": "https://pmvishwakarma.gov.in/"
    },
    {
        "name": "Credit Guarantee Fund Scheme for Micro and Small Enterprises",
        "description": "Collateral-free credit for micro and small enterprises",
        "eligibility": "New and existing MSMEs, manufacturing and service enterprises",
        "benefits": "Credit facility up to ₹2 crores without collateral, government guarantee coverage",
        "category": "msme business_loan collateral_free",
        "source_url": "https://www.cgtmse.in/"
    },
    {
        "name": "Senior Citizens Savings Scheme (SCSS)",
        "description": "Savings scheme for senior citizens with regular income",
        "eligibility": "Indian residents aged 60+ years, civilians aged 55-60 who opt for VRS",
        "benefits": "High interest rate (8.2%), quarterly interest payout, tax deduction under 80C",
        "category": "senior_citizen savings investment pension",
        "source_url": "https://www.indiapost.gov.in/"
    }
]

def scrape_government_schemes(query: str, user_profile: Dict) -> List[Dict]:
    """
    Scrape and filter government schemes based on user query and profile
    Only returns schemes strongly matching the query category
    """
    print(f"Searching schemes for query: {query}")
    print(f"User profile: {user_profile}")
    
    # Normalize query
    query_lower = query.lower()
    
    # Define strict keyword matching
    filtered_schemes = []
    
    for scheme in MOCK_SCHEMES:
        scheme_category = scheme['category'].lower()
        scheme_name = scheme['name'].lower()
        scheme_desc = scheme['description'].lower()
        
        # Calculate match score
        match_score = 0
        query_words = [word for word in query_lower.split() if len(word) > 2]  # Ignore small words
        
        for word in query_words:
            # Strong match in category (highest priority)
            if word in scheme_category:
                match_score += 10
            
            # Match in name (high priority)
            if word in scheme_name:
                match_score += 5
            
            # Match in description (medium priority)
            if word in scheme_desc:
                match_score += 2
        
        # Only include schemes with significant match
        if match_score >= 5:  # Threshold for relevance
            scheme_copy = scheme.copy()
            scheme_copy['initial_match_score'] = match_score
            filtered_schemes.append(scheme_copy)
    
    # Sort by initial match score
    filtered_schemes.sort(key=lambda x: x['initial_match_score'], reverse=True)
    
    print(f"Filtered {len(filtered_schemes)} schemes matching query: {query}")
    for s in filtered_schemes:
        print(f"  - {s['name']} (score: {s['initial_match_score']})")
    
    # If no matches, return empty (don't show irrelevant schemes)
    return filtered_schemes if filtered_schemes else []

def rank_schemes_with_groq(query: str, schemes: List[Dict], user_profile: Dict) -> List[Dict]:
    """
    Use Groq AI to intelligently rank schemes based on user profile and query
    Returns only schemes with 80%+ relevance
    """
    if not schemes:
        return []
    
    try:
        # Prepare context
        user_context = f"""
User Profile:
- Name: {user_profile.get('person_name', 'Not provided')}
- Salary: {user_profile.get('salary', 'Not provided')}
- Company: {user_profile.get('company_name', 'Not provided')}
- Job Role: {user_profile.get('job_role', 'Not provided')}
- Address: {user_profile.get('address', 'Not provided')}
- Total Documents: {user_profile.get('total_documents', 0)}

User Query: "{query}"
CRITICAL: User is specifically and ONLY looking for schemes related to: {query}
"""
        
        schemes_text = "\n\n".join([
            f"Scheme {i}: {s['name']}\nCategory: {s['category']}\nDescription: {s['description']}\nEligibility: {s['eligibility']}\nBenefits: {s['benefits']}"
            for i, s in enumerate(schemes)
        ])
        
        prompt = f"""{user_context}

Available Schemes (Pre-filtered for query relevance):
{schemes_text}

Task: Rank these schemes STRICTLY by how well they match "{query}".

RANKING CRITERIA (in order of importance):
1. Does the scheme DIRECTLY address what user asked for? (90% weight)
2. Is the user eligible based on their profile? (10% weight)

CRITICAL RULES:
- If a scheme is NOT directly related to "{query}", rank it LAST
- If user asks for "pension", ONLY pension/retirement schemes should rank high
- If user asks for "home loan", ONLY housing/property loan schemes should rank high
- Do NOT rank schemes high just because user is eligible if they don't match the query

Return a JSON array of scheme indices (0 to {len(schemes)-1}) ranked from MOST to LEAST relevant to "{query}".

JSON Output:"""

        response = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict financial scheme matcher. Only recommend schemes that DIRECTLY match the user's query. Ignore schemes that don't match even if user is eligible. Return only valid JSON array of indices."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Lower temperature for more focused results
            max_tokens=300
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Clean JSON
        if result_text.startswith("```json"):
            result_text = result_text.replace("```json", "").replace("```", "").strip()
        elif result_text.startswith("```"):
            result_text = result_text.replace("```", "").strip()
        elif result_text.startswith("[") and result_text.endswith("]"):
            pass  # Already clean
        else:
            # Try to extract JSON array
            import re
            match = re.search(r'\[[\d,\s]+\]', result_text)
            if match:
                result_text = match.group()
        
        # Parse ranking
        ranking = json.loads(result_text)
        
        # Reorder schemes based on ranking with relevance threshold
        ranked_schemes = []
        for i, idx in enumerate(ranking):
            if 0 <= idx < len(schemes):
                scheme = schemes[idx].copy()
                # Calculate relevance score (exponential decay for lower ranks)
                relevance_score = 1.0 - (i * 0.15)  # Faster decay
                
                # Only include schemes with 80%+ relevance
                if relevance_score >= 0.80:
                    scheme['relevance_score'] = relevance_score
                    ranked_schemes.append(scheme)
        
        print(f"Returning {len(ranked_schemes)} schemes with 80%+ relevance")
        for s in ranked_schemes:
            print(f"  - {s['name']}: {s['relevance_score']*100:.0f}% match")
        
        return ranked_schemes
        
    except Exception as e:
        print(f"Groq ranking error: {str(e)}")
        # Fallback: return schemes with 80%+ threshold
        filtered = []
        for i, s in enumerate(schemes):
            score = 1.0 - (i * 0.15)
            if score >= 0.80:
                filtered.append({**s, 'relevance_score': score})
        return filtered

def get_recommended_schemes(query: str, user_profile: Dict) -> List[Dict]:
    """
    Main function to get recommended schemes
    """
    # Step 1: Scrape/fetch schemes
    all_schemes = scrape_government_schemes(query, user_profile)
    
    # Step 2: Rank with AI
    ranked_schemes = rank_schemes_with_groq(query, all_schemes, user_profile)
    
    return ranked_schemes
