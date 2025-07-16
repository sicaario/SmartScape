from tavily import TavilyClient
import config
from typing import List, Dict

class ProductSearchService:
    def __init__(self):
        self.client = TavilyClient(api_key=config.TAVILY_API_KEY)
    
    async def search_products(self, suggestions: List[Dict]) -> List[Dict]:
        """Search for products based on room analysis suggestions"""
        products = []
        
        for suggestion in suggestions:
            try:
                # Simplified search queries
                queries = [
                    f"{suggestion['item']} buy online",
                    f"shop {suggestion['item']} home decor"
                ]
                
                for query in queries:
                    try:
                        # Search using Tavily with simplified parameters
                        response = self.client.search(
                            query=query,
                            search_depth="basic",  # Changed from "advanced"
                            max_results=3,
                            # Removed include_domains restriction
                        )
                        
                        # Process results
                        for result in response.get('results', []):
                            url = result.get('url', '')
                            title = result.get('title', '')
                            
                            # Basic filtering for product-like content
                            if title and url:
                                product = {
                                    "title": title,
                                    "url": url,
                                    "description": result.get('content', '')[:200] + "...",
                                    "category": suggestion['category'],
                                    "suggestion_item": suggestion['item'],
                                    "priority": suggestion['priority'],
                                    "source": "tavily_search",
                                    "store": self._extract_store_name(url)
                                }
                                products.append(product)
                        
                        # Limit products per suggestion
                        if len([p for p in products if p['suggestion_item'] == suggestion['item']]) >= 2:
                            break
                            
                    except Exception as e:
                        print(f"Error in Tavily search for query '{query}': {str(e)}")
                        continue
                        
            except Exception as e:
                print(f"Error searching for {suggestion['item']}: {str(e)}")
                continue
        
        # If no products found, add fallback products
        if not products:
            products = self._get_fallback_products(suggestions)
        
        return products
    
    def _get_fallback_products(self, suggestions: List[Dict]) -> List[Dict]:
        """Provide fallback products when Tavily search fails"""
        fallback_products = []
        
        for suggestion in suggestions[:3]:  # Limit to first 3 suggestions
            fallback_products.append({
                "title": f"{suggestion['item'].title()} - Home Decor",
                "url": f"https://www.amazon.com/s?k={suggestion['item'].replace(' ', '+')}",
                "description": f"Find great {suggestion['item']} options for your {suggestion['category']} needs.",
                "category": suggestion['category'],
                "suggestion_item": suggestion['item'],
                "priority": suggestion['priority'],
                "source": "fallback",
                "store": "Amazon"
            })
        
        return fallback_products
    
    def _extract_store_name(self, url: str) -> str:
        """Extract store name from URL"""
        if 'amazon.com' in url:
            return 'Amazon'
        elif 'wayfair.com' in url:
            return 'Wayfair'
        elif 'target.com' in url:
            return 'Target'
        elif 'ikea.com' in url:
            return 'IKEA'
        elif 'homedepot.com' in url:
            return 'Home Depot'
        elif 'lowes.com' in url:
            return 'Lowe\'s'
        elif 'overstock.com' in url:
            return 'Overstock'
        elif 'cb2.com' in url:
            return 'CB2'
        elif 'crateandbarrel.com' in url:
            return 'Crate & Barrel'
        else:
            return 'Online Store'
    
    async def search_specific_product(self, product_name: str, category: str = "") -> List[Dict]:
        """Search for a specific product"""
        try:
            # Simplified query
            query = f"{product_name} {category} buy online"
            
            response = self.client.search(
                query=query,
                search_depth="basic",  # Changed from "advanced"
                max_results=5,
                # Removed include_domains restriction
            )
            
            products = []
            for result in response.get('results', []):
                url = result.get('url', '')
                title = result.get('title', '')
                
                if title and url:
                    product = {
                        "title": title,
                        "url": url,
                        "description": result.get('content', '')[:200] + "...",
                        "category": category,
                        "source": "tavily_search",
                        "store": self._extract_store_name(url)
                    }
                    products.append(product)
            
            # Add fallback if no results
            if not products:
                products.append({
                    "title": f"{product_name.title()} - Search Results",
                    "url": f"https://www.amazon.com/s?k={product_name.replace(' ', '+')}",
                    "description": f"Find {product_name} options online.",
                    "category": category,
                    "source": "fallback",
                    "store": "Amazon"
                })
            
            return products
            
        except Exception as e:
            print(f"Error in specific product search: {str(e)}")
            # Return fallback product
            return [{
                "title": f"{product_name.title()} - Search Results",
                "url": f"https://www.amazon.com/s?k={product_name.replace(' ', '+')}",
                "description": f"Find {product_name} options online.",
                "category": category,
                "source": "fallback",
                "store": "Amazon"
            }]
