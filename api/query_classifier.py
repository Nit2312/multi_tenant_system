"""
Query Classifier for Investment Advisor AI.
Routes queries to the two supported collections: finance and marketing.
"""

import re
from typing import Dict, Tuple

class QueryClassifier:
    """Classifies user queries to determine the appropriate data collection"""
    
    def __init__(self):
        # Define keywords for each category
        self.finance_keywords = {
            'investment', 'invest', 'stock', 'stocks', 'bond', 'bonds', 'portfolio', 
            'dividend', 'roi', 'return', 'profit', 'loss', 'market', 'trading', 
            'share', 'shares', 'equity', 'asset', 'assets', 'wealth', 'financial',
            'money', 'capital', 'value', 'valuation', 'price', 'fund', 'mutual fund',
            'etf', 'index', 'bull', 'bear', 'volatility', 'risk', 'diversification',
            'compound', 'interest', 'inflation', 'recession', 'economy', 'gdp',
            'warren buffett', 'buffett', 'berkshire', 'graham', 'value investing',
            'benjamin graham', 'peter lynch', 'george soros', 'carl icahn',
            # Tax-related keywords
            'tax', 'taxes', 'taxation', 'income tax', 'capital gains tax', 'tax bracket',
            'tax deduction', 'tax credit', 'tax planning', 'tax strategy', 'tax saving',
            'irs', 'tax return', 'tax filing', 'taxable', 'tax-free', 'tax shelter',
            # Rich Dad Poor Dad specific
            'rich dad poor dad', 'robert kiyosaki', 'kiyosaki', 'assets vs liabilities',
            'cash flow', 'financial education', 'financial literacy', 'passive income',
            'real estate investing', 'business ownership', 'entrepreneurship'
        }
        
        self.marketing_keywords = {
            'marketing', 'advertise', 'advertisement', 'campaign', 'brand', 'branding',
            'customer', 'customers', 'client', 'clients', 'lead', 'leads', 'conversion',
            'conversion rate', 'sales funnel', 'acquisition', 'retention', 'churn',
            'social media', 'facebook', 'twitter', 'instagram', 'linkedin', 'content',
            'content marketing', 'email marketing', 'seo', 'sem', 'ppc', 'google ads',
            'facebook ads', 'influencer', 'influencer marketing', 'viral', 'engagement',
            'clickthrough', 'ctr', 'impressions', 'reach', 'traffic', 'landing page',
            # Sales keywords merged into marketing
            'sale', 'sales', 'revenue', 'selling', 'prospect', 'prospecting', 'pipeline',
            'crm', 'customer relationship', 'deal', 'deals', 'closing', 'negotiation',
            'commission', 'quota', 'target', 'forecast', 'lead generation', 'cold call',
            'cold calling', 'follow up', 'follow-up', 'presentation', 'proposal',
            'contract', 'agreement', 'upsell', 'cross-sell', 'account', 'accounts',
            'territory', 'region', 'sales team', 'sales manager', 'b2b', 'b2c',
            # People/influence keywords
            'influence', 'influencing', 'persuade', 'persuasion', 'convince', 'convincing',
            'win people', 'people skills', 'communication', 'negotiating', 'relationships',
            'networking', 'rapport', 'trust', 'credibility', 'leadership', 'motivation'
        }
        
        # Book-specific keywords for metadata filtering
        self.book_keywords = {
            'the education of a value investor': ['education of a value investor', 'value investor education', 'seth klarman'],
            'rich dad poor dad': ['rich dad poor dad', 'robert kiyosaki', 'kiyosaki', 'rich dad', 'poor dad'],
            'the intelligent investor': ['intelligent investor', 'benjamin graham', 'graham', 'mr market'],
            'security analysis': ['security analysis', 'graham', 'dodd'],
            'one up on wall street': ['one up on wall street', 'peter lynch'],
            'common stocks uncommon profits': ['common stocks uncommon profits', 'philip fisher'],
            'the little book of common sense investing': ['little book of common sense', 'john bogle', 'bogle'],
            'a random walk down wall street': ['random walk down wall street', 'burton malkiel'],
            'the essays of warren buffett': ['essays of warren buffett', 'buffett essays', 'berkshire letters'],
            'how to win friends and influence people': ['how to win friends and influence people', 'dale carnegie', 'win friends', 'influence people']
        }
        
        # Investment-specific patterns (Buffett-style wisdom)
        self.investment_patterns = [
            r'warren buffett',
            r'benjamin graham',
            r'value invest',
            r'margin of safety',
            r'intrinsic value',
            r'compound interest',
            r'long term',
            r'buy and hold',
            r'moat',
            r'circle of competence',
            r'mr market',
            r'be fearful when others are greedy',
            r'be greedy when others are fearful'
        ]
    
    def detect_book_specific_query(self, query: str) -> Tuple[bool, str]:
        """
        Detect if query is asking about a specific book
        Returns (is_book_specific, book_name)
        """
        query_lower = query.lower()
        
        for book_name, keywords in self.book_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return True, book_name
        
        return False, ""
    
    def classify_query(self, query: str) -> Tuple[str, float]:
        """
        Classify query into one of: 'finance' or 'marketing'
        Returns tuple of (category, confidence_score)
        """
        query_lower = query.lower()
        
        # Check for investment patterns first (highest priority)
        for pattern in self.investment_patterns:
            if re.search(pattern, query_lower):
                return 'finance', 0.95
        
        # Count keyword matches for each category
        finance_score = self._count_keywords(query_lower, self.finance_keywords)
        marketing_score = self._count_keywords(query_lower, self.marketing_keywords)
        
        # Calculate total and determine best category
        total_score = finance_score + marketing_score
        
        if total_score == 0:
            return 'finance', 0.0  # Default to finance for general queries
        
        # Normalize scores
        finance_confidence = finance_score / total_score
        marketing_confidence = marketing_score / total_score
        
        # Determine category with highest confidence
        if finance_confidence > marketing_confidence:
            return 'finance', finance_confidence
        else:
            return 'marketing', marketing_confidence
    
    def _count_keywords(self, query: str, keywords: set) -> int:
        """Count how many keywords from the set appear in the query"""
        count = 0
        for keyword in keywords:
            if keyword in query:
                count += 1
        return count
    
    def get_collection_name(self, category: str) -> str:
        """Map category to collection name"""
        collection_mapping = {
            'finance': 'finance',
            'marketing': 'marketing'
        }
        return collection_mapping.get(category, 'finance')
    
    def get_fallback_response(self, category: str, query: str) -> str:
        """Generate appropriate response when no relevant data is found"""
        
        if category == 'finance':
            return self._get_buffett_wisdom_response(query)
        elif category == 'marketing':
            return self._get_business_wisdom_response(query, 'marketing')
        else:
            return self._get_general_investment_wisdom(query)
    
    def _get_buffett_wisdom_response(self, query: str) -> str:
        """Generate conversational Warren Buffett-style wisdom response for finance queries"""
        
        query_lower = query.lower()
        
        # Starting investing questions
        if any(word in query_lower for word in ['start investing', 'begin investing', 'how to start', 'getting started']):
            return (
                "Great question! Starting to invest is one of the best financial decisions you can make. "
                "Here's my advice: begin with what you understand. If you understand consumer products, start with companies "
                "that make things you use every day. If you understand technology, look at tech companies you know well. "
                "\n\n"
                "Start small - you don't need thousands of dollars. Even $50 or $100 a month can grow significantly over time "
                "thanks to compound interest. Consider low-cost index funds as a simple way to get started - they give you "
                "diversification across many companies without requiring you to pick individual stocks. "
                "\n\n"
                "Most importantly, focus on learning. Read books, follow companies you're interested in, and understand "
                "what makes a good business. The best investors I know are also the best learners. Remember Rule #1: Never lose money. "
                "Rule #2: Never forget Rule #1!"
            )
        
        # Stock picking questions
        elif any(word in query_lower for word in ['stock', 'stocks', 'invest in', 'buy stocks']):
            return (
                "When it comes to picking stocks, I always tell people to invest within their 'circle of competence' - "
                "meaning businesses and industries you actually understand. Don't buy stock in a company just because "
                "everyone else is excited about it. "
                "\n\n"
                "Look for companies with strong competitive advantages - what I call 'moats.' These could be brand power, "
                "patents, network effects, or cost advantages. Think about whether the company will still be strong in 10-20 years. "
                "\n\n"
                "Price matters too. Even great companies can be bad investments if you overpay. I look for wonderful companies "
                "at fair prices, not fair companies at wonderful prices. Patience is key - sometimes the best move is waiting "
                "for the right price. "
                "\n\n"
                "Remember: 'The stock market is a device for transferring money from the impatient to the patient.'"
            )
        
        # Value investing questions
        elif any(word in query_lower for word in ['value', 'valuation', 'intrinsic value', 'worth']):
            return (
                "Value investing is simple but not easy. The basic idea is buying businesses for less than they're worth. "
                "Think of it like buying a dollar bill for 60 cents - who wouldn't want to do that? "
                "\n\n"
                "To find value, you need to understand what a business is truly worth. This means studying its financials, "
                "competitive position, management quality, and growth prospects. It's more art than science, but the "
                "principles are timeless. "
                "\n\n"
                "My mentor Benjamin Graham taught me to always think about margin of safety - buying at a price low enough "
                "that even if you're wrong about some things, you still won't lose money. This is why I'm always "
                "'fearful when others are greedy and greedy when others are fearful.'"
            )
        
        # Risk and mistakes
        elif any(word in query_lower for word in ['risk', 'mistake', 'wrong', 'lose money']):
            return (
                "Risk comes from not knowing what you're doing - that's one of my most important principles. "
                "The biggest mistake investors make is following trends without understanding what they're buying. "
                "\n\n"
                "Common mistakes I see: market timing (trying to predict short-term movements), over-trading, "
                "investing in things you don't understand, and letting emotions drive decisions. "
                "\n\n"
                "The best way to reduce risk is through knowledge and patience. Understand your investments, "
                "diversify across different companies, and think in terms of years, not months. As I say, "
                "'Someone's sitting in the shade today because someone planted a tree a long time ago.'"
            )
        
        # Tax and Rich Dad Poor Dad questions
        elif any(word in query_lower for word in ['tax', 'taxes', 'taxation', 'income tax', 'capital gains', 'rich dad poor dad', 'robert kiyosaki', 'kiyosaki']):
            return (
                "Robert Kiyosaki taught us some powerful lessons about taxes in 'Rich Dad Poor Dad.' "
                "His key insight: 'The rich don't work for money; they make money work for them.' "
                "When it comes to taxes, the wealthy understand that tax laws are written by the rich, for the rich. "
                "\n\n"
                "Here's what Kiyosaki teaches about taxes:\n"
                "• Employees pay taxes, then live on what's left\n"
                "• Business owners earn, pay taxes, then live on what's left\n"
                "• The wealthy earn, spend, then pay taxes on what's left\n"
                "\n\n"
                "The difference is understanding tax advantages of business ownership, real estate, and investments. "
                "As Kiyosaki says, 'It's not how much money you make, but how much money you keep.' "
                "Focus on building assets that provide tax advantages rather than just earning more income."
            )
        
        # General wisdom
        else:
            return (
                "Investing is simpler than people make it out to be. The key is to buy wonderful businesses "
                "at reasonable prices and hold them for the long term. Don't try to time the market - nobody can "
                "consistently predict short-term movements. "
                "\n\n"
                "Focus on what you can control: your costs, your emotions, and your knowledge. Keep learning, "
                "stay patient, and remember that compounding is the most powerful force in finance. "
                "\n\n"
                "As I always say: 'The best investment you can make is in yourself.' The more you learn, "
                "the better your investment decisions will be."
            )
    
    def _get_business_wisdom_response(self, query: str, domain: str) -> str:
        """Generate business wisdom response for marketing/sales queries"""
        
        if domain == 'marketing':
            return (
                f"Good marketing is about understanding your customers' needs better than anyone else. "
                f"Regarding {query}, remember that the best marketing doesn't feel like marketing - "
                f"it's about building genuine relationships and delivering real value. "
                f"Focus on telling your authentic story and solving real problems."
            )
        else:  # sales
            return (
                f"The best salespeople don't sell products - they solve problems. "
                f"When it comes to {query}, focus on understanding your customer's needs deeply, "
                f"build trust through honesty and expertise, and always prioritize long-term relationships "
                f"over short-term commissions. Great selling is about service, not persuasion."
            )
    
    def _get_general_investment_wisdom(self, query: str) -> str:
        """Generate general investment wisdom"""
        return (
            f"The most important investment you can make is in yourself. "
            f"Regarding {query}, continuous learning and developing your circle of competence "
            f"will serve you better than chasing hot tips or market timing. "
            f"Remember that the best opportunities often come when others are most fearful."
        )
