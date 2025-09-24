import asyncio
import aiohttp
import wikipedia
from duckduckgo_search import DDGS
import json
import re
from typing import List, Dict

class ShoppingSearchEngine:
    def __init__(self):
        self.ddgs = DDGS()
        self.shopping_sites = [
            "amazon.de", "ebay.de", "idealo.de", "otto.de", 
            "mediamarkt.de", "saturn.de", "zalando.de"
        ]
    
    async def search_products(self, product_query: str, max_results: int = 3) -> List[Dict]:
        """Search for specific products with shopping links"""
        print(f"🛒 Shopping search for: {product_query}")
        
        # Create shopping-specific search queries
        shopping_queries = [
            f"{product_query} kaufen",
            f"{product_query} online shop",
            f"{product_query} bestellen"
        ]
        
        all_results = []
        
        for query in shopping_queries:
            try:
                results = self.ddgs.text(query, max_results=5, region='de-de')
                for result in results:
                    url = result.get('href', '')
                    # Filter for shopping sites
                    if any(site in url.lower() for site in self.shopping_sites):
                        all_results.append({
                            'source': 'shopping',
                            'title': result.get('title', ''),
                            'snippet': result.get('body', ''),
                            'url': url,
                            'relevance': 0.9,
                            'site': self.extract_site_name(url),
                            'type': 'product_link'
                        })
            except Exception as e:
                print(f"Shopping search error: {e}")
                continue
        
        # Remove duplicates and rank
        unique_results = self.remove_duplicate_urls(all_results)
        ranked_results = self.rank_shopping_results(unique_results, product_query)
        
        return ranked_results[:max_results]
    
    def extract_site_name(self, url: str) -> str:
        """Extract readable site name from URL"""
        site_names = {
            'amazon.de': 'Amazon',
            'ebay.de': 'eBay', 
            'idealo.de': 'Idealo',
            'otto.de': 'Otto',
            'mediamarkt.de': 'MediaMarkt',
            'saturn.de': 'Saturn',
            'zalando.de': 'Zalando'
        }
        
        for site_url, site_name in site_names.items():
            if site_url in url.lower():
                return site_name
        return "Online Shop"
    
    def remove_duplicate_urls(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate URLs"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result['url']
            if url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    def rank_shopping_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Rank shopping results by relevance"""
        query_words = query.lower().split()
        
        for result in results:
            score = result['relevance']
            content = f"{result['title']} {result['snippet']}".lower()
            
            # Boost for query word matches
            for word in query_words:
                if word in content:
                    score += 0.1
            
            # Boost for popular shopping sites
            popular_sites = ['amazon', 'ebay', 'idealo']
            for site in popular_sites:
                if site in result['url'].lower():
                    score += 0.15
            
            result['relevance'] = min(score, 1.0)
        
        return sorted(results, key=lambda x: x['relevance'], reverse=True)

class UserAwareSearchEngine:
    def __init__(self):
        self.ddgs = DDGS()
        self.shopping_engine = ShoppingSearchEngine()
    
    async def search_for_user(self, query: str, user_type: str, max_results: int = 3) -> List[Dict]:
        """User-specific search routing"""
        
        if user_type == "researcher":
            return await self.academic_search(query, max_results)
        elif user_type == "student":
            return await self.educational_search(query, max_results)
        elif user_type == "business":
            return await self.business_search(query, max_results)
        elif user_type == "shopping":
            return await self.shopping_search(query, max_results)
        else:
            return await self.general_search(query, max_results)
    
    async def shopping_search(self, query: str, max_results: int = 3) -> List[Dict]:
        """Shopping-focused search"""
        
        # Detect if user wants to buy something
        buy_keywords = ['kaufen', 'bestellen', 'buy', 'purchase', 'shopping', 'günstig', 'preis']
        wants_to_buy = any(keyword in query.lower() for keyword in buy_keywords)
        
        if wants_to_buy:
            # Product search
            product_results = await self.shopping_engine.search_products(query, max_results)
            
            # Also get general info about the product
            general_results = await self.general_search(f"{query} test bewertung", 1)
            
            # Combine results
            combined = product_results + general_results
            return combined[:max_results]
        else:
            # General shopping advice/info
            shopping_query = f"{query} shopping guide review"
            return await self.general_search(shopping_query, max_results)
    
    async def academic_search(self, query: str, max_results: int = 3) -> List[Dict]:
        """Academic-focused search with Wikipedia priority"""
        results = []
        
        # Wikipedia first (high relevance for academic)
        try:
            wikipedia.set_lang("en")
            wiki_results = wikipedia.search(query, results=2)
            
            for title in wiki_results:
                try:
                    page = wikipedia.page(title, auto_suggest=False)
                    snippet = page.summary.split('.')[0] + '.'
                    if len(snippet) > 300:
                        snippet = snippet[:300] + "..."
                    
                    results.append({
                        'source': 'wikipedia',
                        'title': page.title,
                        'snippet': snippet,
                        'url': page.url,
                        'relevance': 0.95,  # High relevance for academic
                        'type': 'academic'
                    })
                except:
                    continue
        except Exception as e:
            print(f"Wikipedia search error: {e}")
        
        # Add DuckDuckGo with academic focus
        try:
            academic_query = f"{query} research study academic paper"
            ddg_results = self.ddgs.text(academic_query, max_results=2)
            
            for result in ddg_results:
                results.append({
                    'source': 'duckduckgo',
                    'title': result.get('title', ''),
                    'snippet': result.get('body', ''),
                    'url': result.get('href', ''),
                    'relevance': 0.8,
                    'type': 'academic'
                })
        except Exception as e:
            print(f"Academic search error: {e}")
        
        return self.rank_results(results, query)[:max_results]
    
    async def educational_search(self, query: str, max_results: int = 3) -> List[Dict]:
        """Education-focused search"""
        educational_queries = [
            f"{query} tutorial explanation",
            f"{query} how it works simple",
            f"{query} beginner guide"
        ]
        
        results = []
        for edu_query in educational_queries:
            try:
                search_results = self.ddgs.text(edu_query, max_results=1)
                for result in search_results:
                    results.append({
                        'source': 'duckduckgo',
                        'title': result.get('title', ''),
                        'snippet': result.get('body', ''),
                        'url': result.get('href', ''),
                        'relevance': 0.85,
                        'type': 'educational'
                    })
            except Exception as e:
                print(f"Educational search error: {e}")
                continue
        
        return self.rank_results(results, query)[:max_results]
    
    async def business_search(self, query: str, max_results: int = 3) -> List[Dict]:
        """Business-focused search"""
        business_query = f"{query} business market trends analysis 2024"
        
        try:
            results = []
            search_results = self.ddgs.text(business_query, max_results=max_results)
            
            for result in search_results:
                results.append({
                    'source': 'duckduckgo',
                    'title': result.get('title', ''),
                    'snippet': result.get('body', ''),
                    'url': result.get('href', ''),
                    'relevance': 0.8,
                    'type': 'business'
                })
            
            return self.rank_results(results, query)
        except Exception as e:
            print(f"Business search error: {e}")
            return []
    
    async def general_search(self, query: str, max_results: int = 3) -> List[Dict]:
        """General search fallback"""
        try:
            results = []
            search_results = self.ddgs.text(query, max_results=max_results)
            
            for result in search_results:
                results.append({
                    'source': 'duckduckgo',
                    'title': result.get('title', ''),
                    'snippet': result.get('body', ''),
                    'url': result.get('href', ''),
                    'relevance': 0.7,
                    'type': 'general'
                })
            
            return results
        except Exception as e:
            print(f"General search error: {e}")
            return []
    
    def rank_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Rank results by relevance"""
        query_words = query.lower().split()
        
        for result in results:
            score = result['relevance']
            content = f"{result['title']} {result['snippet']}".lower()
            
            for word in query_words:
                if word in content:
                    score += 0.1
            
            result['relevance'] = min(score, 1.0)
        
        return sorted(results, key=lambda x: x['relevance'], reverse=True)