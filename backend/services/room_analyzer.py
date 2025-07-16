import config  # This imports and loads environment variables
from openai import OpenAI
import json
import base64
from typing import Dict

class RoomAnalyzer:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://api.studio.nebius.ai/v1/",
            api_key=config.NEBIUS_API_KEY
        )
    
    async def analyze_room_image(self, image_data: bytes) -> Dict:
        """Analyze room image and provide decoration suggestions using Nebius vision model"""
        try:
            # Convert image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            prompt = """
            Analyze this room image and provide specific home decoration suggestions to make it more cozy and inviting. 
            
            Please provide your response in the following JSON format:
            {
                "room_type": "bedroom/living_room/kitchen/etc",
                "current_style": "description of current style",
                "suggestions": [
                    {
                        "category": "lighting/furniture/decor/plants/textiles",
                        "item": "specific item name",
                        "description": "why this would improve the space",
                        "priority": "high/medium/low"
                    }
                ],
                "color_palette": ["color1", "color2", "color3"],
                "overall_assessment": "brief description of the room's potential"
            }
            
            Focus on practical, achievable improvements that would make the space more comfortable and aesthetically pleasing.
            """
            
            response = self.client.chat.completions.create(
                model="Qwen/Qwen2-VL-72B-Instruct",
                max_tokens=1024,
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
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ]
            )
            
            # Get the response text
            analysis_text = response.choices[0].message.content
            
            # Try to parse JSON from the response
            try:
                # Look for JSON in the response
                start_idx = analysis_text.find('{')
                end_idx = analysis_text.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = analysis_text[start_idx:end_idx]
                    parsed_analysis = json.loads(json_str)
                    parsed_analysis["ai_response"] = analysis_text
                    return parsed_analysis
            except json.JSONDecodeError:
                pass
            
            # Fallback structured response if JSON parsing fails
            return {
                "room_type": "living_room",
                "current_style": "modern with potential for warmth",
                "suggestions": [
                    {
                        "category": "lighting",
                        "item": "warm table lamps",
                        "description": "Add ambient lighting to create a cozy atmosphere",
                        "priority": "high"
                    },
                    {
                        "category": "textiles",
                        "item": "throw pillows and blankets",
                        "description": "Soft textures will make the space more inviting",
                        "priority": "high"
                    },
                    {
                        "category": "plants",
                        "item": "indoor plants",
                        "description": "Add life and natural elements to the space",
                        "priority": "medium"
                    }
                ],
                "color_palette": ["warm beige", "soft gray", "forest green"],
                "overall_assessment": "Great potential for creating a cozy, welcoming space",
                "ai_response": analysis_text
            }
            
        except Exception as e:
            raise Exception(f"Error analyzing room with Nebius API: {str(e)}")