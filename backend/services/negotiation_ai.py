import config
from openai import OpenAI
import json
from typing import Dict, List
import time
from datetime import datetime, timedelta

class NegotiationAI:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://api.studio.nebius.ai/v1/",
            api_key=config.NEBIUS_API_KEY
        )
        
        # Store conversation history
        self.conversations = {}
        
    def handle_buyer_message(self, listing_id: str, buyer_message: str, listing_data: Dict, conversation_history: List = None):
        """Generate AI response to buyer message"""
        
        if conversation_history is None:
            conversation_history = []
            
        try:
            # Build context about the item
            item_context = f"""
            Item: {listing_data['title']}
            Listed Price: ${listing_data['price']}
            Minimum Price: ${listing_data.get('min_price', listing_data['price'] * 0.7)}
            Condition: {listing_data.get('condition', 'good')}
            Description: {listing_data['description']}
            """
            
            # Build conversation context
            conversation_context = ""
            if conversation_history:
                conversation_context = "\nPrevious conversation:\n"
                for msg in conversation_history[-5:]:  # Last 5 messages
                    role = "Buyer" if msg['role'] == 'buyer' else "You"
                    conversation_context += f"{role}: {msg['message']}\n"
            
            prompt = f"""
            You are a friendly seller on Facebook Marketplace. A buyer has sent you a message about your listing.
            
            {item_context}
            {conversation_context}
            
            Buyer's latest message: "{buyer_message}"
            
            Guidelines:
            - Be friendly and professional
            - If they ask about price, you can negotiate but don't go below your minimum
            - If they want to meet, suggest a safe public location
            - If they seem serious, try to close the deal
            - Answer questions about the item honestly
            - If they make a reasonable offer, consider accepting or counter-offering
            
            Respond naturally as a seller would. Keep it conversational and helpful.
            
            Also determine what action to take:
            - "negotiate" if discussing price
            - "schedule" if they want to meet
            - "answer" if just answering questions
            - "accept" if accepting their offer
            - "decline" if declining their offer
            
            Return JSON:
            {{
                "response": "your message to the buyer",
                "action": "negotiate|schedule|answer|accept|decline",
                "suggested_price": null or price if counter-offering,
                "confidence": 0.8,
                "next_steps": "brief note about what should happen next"
            }}
            """
            
            response = self.client.chat.completions.create(
                model="Qwen/Qwen2-VL-72B-Instruct",
                max_tokens=512,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            ai_response = response.choices[0].message.content
            
            try:
                # Parse JSON response
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = ai_response[start_idx:end_idx]
                    result = json.loads(json_str)
                else:
                    raise json.JSONDecodeError("No JSON found", "", 0)
                    
            except json.JSONDecodeError:
                # Fallback response
                result = {
                    "response": ai_response,
                    "action": "answer",
                    "suggested_price": None,
                    "confidence": 0.7,
                    "next_steps": "Continue conversation"
                }
            
            # Store conversation
            if listing_id not in self.conversations:
                self.conversations[listing_id] = []
                
            self.conversations[listing_id].extend([
                {"role": "buyer", "message": buyer_message, "timestamp": datetime.now().isoformat()},
                {"role": "seller", "message": result["response"], "timestamp": datetime.now().isoformat()}
            ])
            
            return {
                "listing_id": listing_id,
                "ai_response": result["response"],
                "action": result["action"],
                "suggested_price": result.get("suggested_price"),
                "confidence": result.get("confidence", 0.7),
                "next_steps": result.get("next_steps", ""),
                "conversation_history": self.conversations[listing_id]
            }
            
        except Exception as e:
            raise Exception(f"Error generating AI response: {str(e)}")
    
    def suggest_meetup_time(self, buyer_message: str, seller_availability: Dict = None):
        """Suggest meeting times based on buyer request"""
        
        try:
            # Default availability if none provided
            if seller_availability is None:
                seller_availability = {
                    "weekdays": ["10:00-18:00"],
                    "weekends": ["09:00-17:00"],
                    "timezone": "local"
                }
            
            prompt = f"""
            A buyer wants to meet up to purchase an item. Based on their message, suggest 2-3 good meeting times.
            
            Buyer message: "{buyer_message}"
            
            Seller availability:
            - Weekdays: {seller_availability.get('weekdays', ['10:00-18:00'])}
            - Weekends: {seller_availability.get('weekends', ['09:00-17:00'])}
            
            Current date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            
            Suggest meeting times in the next 3-7 days. Always suggest safe public locations like:
            - Coffee shops
            - Shopping mall parking lots
            - Police station parking lots
            - Busy public areas
            
            Return JSON:
            {{
                "suggested_times": [
                    {{"day": "Monday", "date": "2024-01-15", "time": "2:00 PM", "location": "Starbucks on Main St"}},
                    {{"day": "Wednesday", "date": "2024-01-17", "time": "11:00 AM", "location": "Target parking lot"}}
                ],
                "message": "friendly message suggesting these times"
            }}
            """
            
            response = self.client.chat.completions.create(
                model="Qwen/Qwen2-VL-72B-Instruct",
                max_tokens=512,
                temperature=0.6,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            ai_response = response.choices[0].message.content
            
            try:
                # Parse JSON response
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = ai_response[start_idx:end_idx]
                    result = json.loads(json_str)
                else:
                    raise json.JSONDecodeError("No JSON found", "", 0)
                    
            except json.JSONDecodeError:
                # Fallback response
                tomorrow = datetime.now() + timedelta(days=1)
                result = {
                    "suggested_times": [
                        {
                            "day": tomorrow.strftime('%A'),
                            "date": tomorrow.strftime('%Y-%m-%d'),
                            "time": "2:00 PM",
                            "location": "Local coffee shop"
                        }
                    ],
                    "message": "How about tomorrow at 2 PM? We can meet at a local coffee shop."
                }
            
            return result
            
        except Exception as e:
            raise Exception(f"Error suggesting meetup time: {str(e)}")
    
    def get_conversation_history(self, listing_id: str):
        """Get conversation history for a listing"""
        return self.conversations.get(listing_id, [])
    
    def analyze_buyer_intent(self, message: str):
        """Analyze what the buyer wants"""
        
        message_lower = message.lower()
        
        # Simple intent detection
        if any(word in message_lower for word in ['price', 'cost', 'much', 'expensive', 'cheap', 'deal']):
            return 'price_inquiry'
        elif any(word in message_lower for word in ['meet', 'pickup', 'when', 'where', 'available']):
            return 'meetup_request'
        elif any(word in message_lower for word in ['condition', 'quality', 'damage', 'work', 'broken']):
            return 'condition_inquiry'
        elif any(word in message_lower for word in ['buy', 'take', 'purchase', 'interested', 'want']):
            return 'purchase_intent'
        else:
            return 'general_inquiry'
