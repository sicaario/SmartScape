import os
from mem0 import MemoryClient
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

class Mem0Service:
    """Service for managing user preferences and personalization using mem0"""
    
    def __init__(self):
        """Initialize mem0 client"""
        api_key = os.getenv("MEM0_API_KEY")
        if not api_key:
            raise ValueError("MEM0_API_KEY environment variable is required")
        
        self.memory = MemoryClient(api_key=api_key)
        print(f"Mem0Service initialized successfully")
    
    async def store_room_analysis_preference(self, user_id: str, room_analysis: Dict[str, Any], user_feedback: Optional[str] = None):
        """Store user's room analysis history and preferences"""
        try:
            # Create memory content about user's room preferences
            room_type = room_analysis.get('room_type', 'unknown')
            current_style = room_analysis.get('current_style', 'unknown')
            suggestions = room_analysis.get('suggestions', [])
            
            memory_content = f"User analyzed a {room_type} with {current_style} style. "
            memory_content += f"Room analysis suggested: {', '.join(suggestions[:3])}. "
            
            if user_feedback:
                memory_content += f"User feedback: {user_feedback}. "
            
            memory_content += f"Analysis date: {datetime.now().isoformat()}"
            
            metadata = {
                "type": "room_analysis",
                "room_type": room_type,
                "style": current_style,
                "timestamp": datetime.now().isoformat()
            }
            
            # DEBUG: Print what we're sending to mem0
            print(f"=== MEM0 DEBUG: store_room_analysis_preference ===")
            print(f"User ID: {user_id}")
            print(f"Sending to mem0: {memory_content}")
            print(f"Metadata: {metadata}")
            print(f"=== END MEM0 DEBUG ===")
            
            # Store in mem0
            result = self.memory.add(
                messages=[{"role": "user", "content": memory_content}],
                user_id=user_id,
                metadata=metadata
            )
            
            print(f"Mem0 response: {result}")
            print(f"Stored room analysis preference for user {user_id}")
            return result
            
        except Exception as e:
            print(f"Error storing room analysis preference: {str(e)}")
            return None
    
    async def store_saved_item_preference(self, user_id: str, product_data: Dict[str, Any]):
        """Store user's saved item preferences"""
        try:
            product_name = product_data.get('name', 'unknown product')
            category = product_data.get('category', 'unknown')
            price_range = product_data.get('price', 'unknown')
            
            memory_content = f"User saved {product_name} in {category} category with price {price_range}. "
            memory_content += f"This indicates interest in {category} items. "
            memory_content += f"Saved on: {datetime.now().isoformat()}"
            
            metadata = {
                "type": "saved_item",
                "category": category,
                "product_name": product_name,
                "timestamp": datetime.now().isoformat()
            }
            
            # DEBUG: Print what we're sending to mem0
            print(f"=== MEM0 DEBUG: store_saved_item_preference ===")
            print(f"User ID: {user_id}")
            print(f"Sending to mem0: {memory_content}")
            print(f"Metadata: {metadata}")
            print(f"=== END MEM0 DEBUG ===")
            
            result = self.memory.add(
                messages=[{"role": "user", "content": memory_content}],
                user_id=user_id,
                metadata=metadata
            )
            
            print(f"Mem0 response: {result}")
            print(f"Stored saved item preference for user {user_id}")
            return result
            
        except Exception as e:
            print(f"Error storing saved item preference: {str(e)}")
            return None
    
    async def store_rejected_suggestion(self, user_id: str, rejected_item: Dict[str, Any], reason: Optional[str] = None):
        """Store rejected suggestions to avoid repeating them"""
        try:
            item_name = rejected_item.get('name', 'unknown item')
            category = rejected_item.get('category', 'unknown')
            
            memory_content = f"User rejected suggestion: {item_name} in {category} category. "
            if reason:
                memory_content += f"Reason: {reason}. "
            memory_content += f"Avoid suggesting similar {category} items. "
            memory_content += f"Rejected on: {datetime.now().isoformat()}"
            
            result = self.memory.add(
                messages=[{"role": "user", "content": memory_content}],
                user_id=user_id,
                metadata={
                    "type": "rejected_suggestion",
                    "category": category,
                    "item_name": item_name,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            print(f"Stored rejected suggestion for user {user_id}")
            return result
            
        except Exception as e:
            print(f"Error storing rejected suggestion: {str(e)}")
            return None
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences and history for personalized recommendations"""
        try:
            # Search for user's memories
            memories = self.memory.search(
                query="user preferences room style saved items rejected suggestions",
                user_id=user_id,
                limit=50
            )
            
            preferences = {
                "preferred_styles": [],
                "preferred_categories": [],
                "rejected_categories": [],
                "room_types_analyzed": [],
                "recent_interests": []
            }
            
            for memory in memories:
                metadata = memory.get('metadata', {})
                memory_type = metadata.get('type', '')
                
                if memory_type == 'room_analysis':
                    style = metadata.get('style')
                    room_type = metadata.get('room_type')
                    if style and style not in preferences["preferred_styles"]:
                        preferences["preferred_styles"].append(style)
                    if room_type and room_type not in preferences["room_types_analyzed"]:
                        preferences["room_types_analyzed"].append(room_type)
                
                elif memory_type == 'saved_item':
                    category = metadata.get('category')
                    if category and category not in preferences["preferred_categories"]:
                        preferences["preferred_categories"].append(category)
                        preferences["recent_interests"].append(category)
                
                elif memory_type == 'rejected_suggestion':
                    category = metadata.get('category')
                    if category and category not in preferences["rejected_categories"]:
                        preferences["rejected_categories"].append(category)
            
            print(f"Retrieved preferences for user {user_id}: {preferences}")
            return preferences
            
        except Exception as e:
            print(f"Error getting user preferences: {str(e)}")
            return {
                "preferred_styles": [],
                "preferred_categories": [],
                "rejected_categories": [],
                "room_types_analyzed": [],
                "recent_interests": []
            }
    
    async def get_personalized_suggestions(self, user_id: str, room_type: str, current_suggestions: List[str]) -> List[str]:
        """Get personalized suggestions based on user history"""
        try:
            preferences = await self.get_user_preferences(user_id)
            
            # Filter out rejected categories
            filtered_suggestions = []
            for suggestion in current_suggestions:
                should_include = True
                for rejected_category in preferences["rejected_categories"]:
                    if rejected_category.lower() in suggestion.lower():
                        should_include = False
                        break
                if should_include:
                    filtered_suggestions.append(suggestion)
            
            # Add personalized suggestions based on preferred categories
            personalized_additions = []
            for preferred_category in preferences["preferred_categories"]:
                if preferred_category not in [s.lower() for s in filtered_suggestions]:
                    personalized_additions.append(f"{preferred_category} items for {room_type}")
            
            # Combine and prioritize
            final_suggestions = filtered_suggestions + personalized_additions[:2]  # Limit additions
            
            print(f"Generated personalized suggestions for user {user_id}: {final_suggestions}")
            return final_suggestions
            
        except Exception as e:
            print(f"Error generating personalized suggestions: {str(e)}")
            return current_suggestions  # Fallback to original suggestions
    
    async def learn_from_interaction(self, user_id: str, interaction_type: str, interaction_data: Dict[str, Any]):
        """Learn from user interactions to improve future recommendations"""
        try:
            timestamp = datetime.now().isoformat()
            
            if interaction_type == "product_search":
                query = interaction_data.get('query', '')
                category = interaction_data.get('category', '')
                memory_content = f"User searched for '{query}' in {category} category. Shows interest in {category} items. Search date: {timestamp}"
                
            elif interaction_type == "room_suggestion_view":
                room_type = interaction_data.get('room_type', '')
                memory_content = f"User viewed suggestions for {room_type}. Interested in {room_type} decoration. View date: {timestamp}"
                
            elif interaction_type == "item_click":
                item_name = interaction_data.get('item_name', '')
                category = interaction_data.get('category', '')
                memory_content = f"User clicked on {item_name} in {category} category. Shows engagement with {category} items. Click date: {timestamp}"
                
            else:
                memory_content = f"User interaction: {interaction_type} with data: {json.dumps(interaction_data)}. Date: {timestamp}"
            
            metadata = {
                "type": "interaction",
                "interaction_type": interaction_type,
                "timestamp": timestamp
            }
            
            # DEBUG: Print what we're sending to mem0
            print(f"=== MEM0 DEBUG: learn_from_interaction ===")
            print(f"User ID: {user_id}")
            print(f"Interaction Type: {interaction_type}")
            print(f"Sending to mem0: {memory_content}")
            print(f"Metadata: {metadata}")
            print(f"=== END MEM0 DEBUG ===")
            
            result = self.memory.add(
                messages=[{"role": "user", "content": memory_content}],
                user_id=user_id,
                metadata=metadata
            )
            
            print(f"Mem0 response: {result}")
            print(f"Learned from interaction for user {user_id}: {interaction_type}")
            return result
            
        except Exception as e:
            print(f"Error learning from interaction: {str(e)}")
            return None
