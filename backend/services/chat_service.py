import asyncio
from typing import Dict, List, Any
import config
from services.mem0_service import Mem0Service
from services.product_search import ProductSearchService
from openai import OpenAI

class ChatService:
    """Service for handling intelligent chat interactions with Mem0 and Tavily"""
    
    def __init__(self):
        self.conversation_history = {}
        
        # Initialize Nebius AI client
        self.ai_client = OpenAI(
            base_url="https://api.studio.nebius.ai/v1/",
            api_key=config.NEBIUS_API_KEY
        )
        
        # Initialize Mem0 service
        try:
            self.mem0_service = Mem0Service()
            self.mem0_enabled = True
            print("ChatService: Mem0 service enabled")
        except Exception as e:
            print(f"ChatService: Mem0 service not available: {str(e)}")
            self.mem0_service = None
            self.mem0_enabled = False
        
        # Initialize product search
        self.product_search = ProductSearchService()
    
    async def handle_chat_message(self, user_id: str, message: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Handle chat message with intelligent AI responses using Nebius"""
        
        try:
            # Get user preferences from Mem0
            user_preferences = {}
            if self.mem0_enabled and self.mem0_service:
                try:
                    user_preferences = await self.mem0_service.get_user_preferences(user_id)
                    print(f"Retrieved user preferences: {user_preferences}")
                except Exception as e:
                    print(f"Error getting user preferences: {str(e)}")
            
            # Build context for AI
            context = self._build_ai_context(user_preferences, conversation_history)
            
            # Generate AI response using Nebius
            ai_response = await self._generate_ai_response(message, context)
            
            # Check if user is asking about products and search if needed
            if any(word in message.lower() for word in ["find", "search", "buy", "where", "furniture", "chair", "sofa", "table", "bed", "lamp", "lighting", "decor", "plants", "rug", "curtains", "mirror"]):
                try:
                    # Extract product query from message
                    product_query = self._extract_product_query(message)
                    if product_query:
                        products = await self.product_search.search_specific_product(product_query, "home decor")
                        if products:
                            ai_response += f"\n\nI found some great {product_query} options for you:\n"
                            for i, product in enumerate(products[:3], 1):
                                ai_response += f"{i}. **{product['title']}** - {product['store']}\n"
                                ai_response += f"   {product['url']}\n"
                except Exception as e:
                    print(f"Error searching products: {str(e)}")
            
            # Learn from this interaction
            if self.mem0_enabled and self.mem0_service:
                try:
                    await self.mem0_service.learn_from_interaction(user_id, "chat_message", {
                        "message": message,
                        "response_type": "ai_chat_response"
                    })
                except Exception as e:
                    print(f"Error learning from interaction: {str(e)}")
            
            return {
                "response": ai_response,
                "suggested_actions": [],
                "user_preferences_used": bool(user_preferences),
                "mem0_enabled": self.mem0_enabled
            }
            
        except Exception as e:
            print(f"Error in chat service: {str(e)}")
            return {
                "response": "Sorry, I'm having trouble right now. Please try again!",
                "suggested_actions": [],
                "user_preferences_used": False,
                "mem0_enabled": False
            }
    
    async def _generate_ai_response(self, message: str, context: str) -> str:
        """Generate AI response using Nebius"""
        
        try:
            system_prompt = f"""You are SmartScape, an AI home concierge assistant. You help users make their spaces more cozy and beautiful.

Context about the user:
{context}

Guidelines:
- Be friendly, helpful, and enthusiastic about home decoration
- Give specific, actionable advice
- Ask follow-up questions to better understand their needs
- If they ask about products, suggest specific items and where to find them
- Keep responses conversational and not too long
- Use emojis sparingly but appropriately 🏡✨

Respond to the user's message in a helpful, personalized way."""

            response = self.ai_client.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3",
                max_tokens=512,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating AI response: {str(e)}")
            return "I'd love to help you with your home decoration! Could you tell me more about what you're looking for?"
    
    def _build_ai_context(self, user_preferences: Dict, conversation_history: List[Dict] = None) -> str:
        """Build context string for AI from user preferences and history"""
        
        context_parts = []
        
        if user_preferences.get("preferred_styles"):
            styles = ", ".join(user_preferences["preferred_styles"])
            context_parts.append(f"User prefers {styles} style")
        
        if user_preferences.get("preferred_categories"):
            categories = ", ".join(user_preferences["preferred_categories"])
            context_parts.append(f"User is interested in {categories}")
        
        if user_preferences.get("room_types_analyzed"):
            rooms = ", ".join(user_preferences["room_types_analyzed"])
            context_parts.append(f"User has worked on {rooms}")
        
        if conversation_history:
            recent_messages = conversation_history[-3:]  # Last 3 messages for context
            context_parts.append("Recent conversation:")
            for msg in recent_messages:
                context_parts.append(f"- {msg.get('type', 'user')}: {msg.get('content', '')[:100]}")
        
        return "\n".join(context_parts) if context_parts else "No previous context available"
    
    def _extract_product_query(self, message: str) -> str:
        """Extract product search query from user message"""
        
        # Simple keyword extraction - could be improved with NLP
        product_keywords = ["chair", "sofa", "table", "bed", "lamp", "lighting", "decor", "plants", "rug", "curtains", "mirror", "furniture"]
        
        message_lower = message.lower()
        for keyword in product_keywords:
            if keyword in message_lower:
                return keyword
        
        # If no specific product found, return general query
        if any(word in message_lower for word in ["find", "search", "buy", "where"]):
            return "home decor"
        
        return None
    
    async def search_products_for_chat(self, user_id: str, query: str) -> Dict[str, Any]:
        """Search products for chat interface"""
        
        try:
            products = await self.product_search.search_specific_product(query, "home decor")
            
            return {
                "success": True,
                "products": products,
                "query": query
            }
            
        except Exception as e:
            print(f"Error searching products: {str(e)}")
            return {
                "success": False,
                "products": [],
                "query": query,
                "error": str(e)
            }
    
    async def save_chat_preference(self, user_id: str, preference_type: str, preference_value: str) -> bool:
        """Save user preference from chat"""
        
        try:
            if self.mem0_enabled and self.mem0_service:
                await self.mem0_service.learn_from_interaction(user_id, "preference_update", {
                    "preference_type": preference_type,
                    "preference_value": preference_value
                })
                return True
            else:
                print(f"Saving preference for {user_id}: {preference_type} = {preference_value}")
                return True
            
        except Exception as e:
            print(f"Error saving preference: {str(e)}")
            return False
