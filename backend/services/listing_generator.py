import config
from openai import OpenAI
import json
from typing import Dict, List
import uuid

class ListingGenerator:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://api.studio.nebius.ai/v1/",
            api_key=config.NEBIUS_API_KEY
        )
        
        # Store active negotiations
        self.negotiations = {}
    
    async def create_listing(self, item: Dict) -> Dict:
        """Generate marketplace listing for an item"""
        
        try:
            prompt = f"""
            Create a compelling marketplace listing for this item:
            
            Item: {item['name']}
            Category: {item['category']}
            Estimated Price: ${item['estimated_price']}
            Condition: {item['condition']}
            
            Generate a JSON response with:
            {{
                "title": "catchy marketplace title (max 80 chars)",
                "description": "detailed description highlighting features and condition",
                "price": "suggested listing price",
                "min_price": "minimum acceptable price for negotiations",
                "keywords": ["keyword1", "keyword2", "keyword3"],
                "condition_details": "specific condition notes"
            }}
            
            Make it appealing to buyers while being honest about condition.
            """
            
            response = self.client.chat.completions.create(
                model="Qwen/Qwen2-VL-72B-Instruct",
                max_tokens=512,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{item['frame_data']}"
                                }
                            }
                        ]
                    }
                ]
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            
            try:
                # Extract JSON from response
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = ai_response[start_idx:end_idx]
                    listing_data = json.loads(json_str)
                else:
                    raise json.JSONDecodeError("No JSON found", "", 0)
                    
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                listing_data = {
                    "title": f"{item['name'].title()} - {item['condition'].title()} Condition",
                    "description": f"A {item['name']} in {item['condition']} condition. Perfect for your home!",
                    "price": item['estimated_price'],
                    "min_price": round(item['estimated_price'] * 0.7, 2),
                    "keywords": [item['name'], item['category'], item['condition']],
                    "condition_details": f"Item is in {item['condition']} condition"
                }
            
            # Create complete listing
            listing = {
                "id": str(uuid.uuid4()),
                "item_id": item['id'],
                "title": listing_data.get("title", ""),
                "description": listing_data.get("description", ""),
                "price": float(listing_data.get("price", item['estimated_price'])),
                "min_price": float(listing_data.get("min_price", item['estimated_price'] * 0.7)),
                "keywords": listing_data.get("keywords", []),
                "condition": item['condition'],
                "condition_details": listing_data.get("condition_details", ""),
                "category": item['category'],
                "image_data": item['frame_data'],
                "timestamp": item['timestamp'],
                "status": "draft",
                "ai_response": ai_response
            }
            
            return listing
            
        except Exception as e:
            raise Exception(f"Error creating listing: {str(e)}")
    
    async def handle_negotiation(self, listing_id: str, buyer_message: str, current_price: float) -> Dict:
        """Handle buyer negotiation using AI"""
        
        try:
            # Get or create negotiation context
            if listing_id not in self.negotiations:
                self.negotiations[listing_id] = {
                    "messages": [],
                    "current_price": current_price,
                    "min_price": current_price * 0.7  # Default 30% discount limit
                }
            
            negotiation = self.negotiations[listing_id]
            negotiation["messages"].append({"role": "buyer", "message": buyer_message})
            
            prompt = f"""
            You are a friendly seller negotiating the price of an item. 
            
            Current asking price: ${current_price}
            Minimum acceptable price: ${negotiation['min_price']}
            Buyer's message: "{buyer_message}"
            
            Previous conversation:
            {self._format_conversation(negotiation['messages'][-3:])}
            
            Respond as the seller. Be friendly but firm about your minimum price.
            If the buyer's offer is above your minimum, consider accepting or making a counteroffer.
            If it's too low, politely decline and suggest a reasonable counteroffer.
            
            Respond in JSON format:
            {{
                "response": "your response to the buyer",
                "action": "accept|counteroffer|decline",
                "suggested_price": "price if making counteroffer",
                "reasoning": "brief explanation of your decision"
            }}
            """
            
            response = self.client.chat.completions.create(
                model="Qwen/Qwen2-VL-72B-Instruct",
                max_tokens=256,
                temperature=0.8,
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
                    negotiation_result = json.loads(json_str)
                else:
                    raise json.JSONDecodeError("No JSON found", "", 0)
                    
            except json.JSONDecodeError:
                # Fallback response
                negotiation_result = {
                    "response": "Thanks for your interest! Let me know if you'd like to discuss the price.",
                    "action": "counteroffer",
                    "suggested_price": current_price * 0.9,
                    "reasoning": "Standard response due to parsing error"
                }
            
            # Store seller response
            negotiation["messages"].append({
                "role": "seller", 
                "message": negotiation_result.get("response", "")
            })
            
            return {
                "listing_id": listing_id,
                "seller_response": negotiation_result.get("response", ""),
                "action": negotiation_result.get("action", "counteroffer"),
                "suggested_price": negotiation_result.get("suggested_price"),
                "reasoning": negotiation_result.get("reasoning", ""),
                "conversation": negotiation["messages"]
            }
            
        except Exception as e:
            raise Exception(f"Error handling negotiation: {str(e)}")
    
    def _format_conversation(self, messages: List[Dict]) -> str:
        """Format conversation history for AI prompt"""
        
        formatted = []
        for msg in messages:
            role = msg["role"].title()
            formatted.append(f"{role}: {msg['message']}")
        
        return "\n".join(formatted) if formatted else "No previous conversation"
