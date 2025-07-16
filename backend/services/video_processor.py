import config
from openai import OpenAI
import base64
import json
from typing import List, Dict
import tempfile
import os
import cv2
import numpy as np

class VideoProcessor:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://api.studio.nebius.ai/v1/",
            api_key=config.NEBIUS_API_KEY
        )
        
        # Common sellable household items for suggestions
        self.sellable_categories = {
            'furniture': ['chair', 'table', 'sofa', 'bed', 'desk', 'bookshelf', 'dresser', 'cabinet'],
            'electronics': ['tv', 'laptop', 'monitor', 'speaker', 'phone', 'tablet', 'camera'],
            'appliances': ['microwave', 'toaster', 'blender', 'coffee maker', 'vacuum'],
            'decor': ['lamp', 'mirror', 'picture frame', 'vase', 'clock', 'plant pot'],
            'sports': ['bicycle', 'exercise equipment', 'sports gear'],
            'books': ['book', 'magazine'],
            'clothing': ['jacket', 'shoes', 'bag', 'backpack']
        }
    
    async def extract_frames(self, video_data: bytes) -> List[Dict]:
        """Extract actual frames from video using OpenCV"""
        
        try:
            # Save video data to temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                temp_file.write(video_data)
                temp_video_path = temp_file.name
            
            # Open video with OpenCV
            cap = cv2.VideoCapture(temp_video_path)
            
            if not cap.isOpened():
                raise Exception("Could not open video file")
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            print(f"Video info: {fps} FPS, {total_frames} frames, {duration:.2f}s duration")
            
            frames = []
            frame_interval = max(1, int(fps * 2))  # Extract frame every 2 seconds
            
            frame_count = 0
            extracted_count = 0
            
            while cap.isOpened() and extracted_count < 5:  # Limit to 5 frames
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Extract frame at intervals
                if frame_count % frame_interval == 0:
                    # Convert frame to JPEG
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    timestamp = frame_count / fps if fps > 0 else extracted_count * 2
                    
                    frames.append({
                        'id': f"frame_{extracted_count}",
                        'timestamp': timestamp,
                        'frame_data': frame_base64,
                        'frame_number': frame_count,
                        'items': []
                    })
                    
                    extracted_count += 1
                    print(f"Extracted frame {extracted_count} at {timestamp:.1f}s")
                
                frame_count += 1
            
            cap.release()
            
            # Clean up temporary file
            try:
                os.unlink(temp_video_path)
            except:
                pass
            
            print(f"Extracted {len(frames)} frames from video")
            return frames
            
        except Exception as e:
            raise Exception(f"Error extracting frames: {str(e)}")
    
    async def detect_objects(self, frames: List[Dict]) -> List[Dict]:
        """Detect objects in video frames using Nebius vision model"""
        
        detected_objects = []
        
        for frame_info in frames:
            try:
                prompt = """
                Analyze this video frame and identify sellable household items that could be sold on a marketplace.
                
                Look for items like:
                - Furniture (chairs, tables, sofas, beds, desks, bookshelves)
                - Electronics (TVs, laptops, monitors, speakers, phones, tablets)
                - Appliances (microwaves, toasters, blenders, coffee makers)
                - Decor items (lamps, mirrors, picture frames, vases, clocks)
                - Sports equipment (bicycles, exercise equipment)
                - Books and magazines
                - Clothing and accessories (jackets, shoes, bags)
                
                Return a JSON array of detected sellable items:
                [
                    {
                        "object_name": "specific item name",
                        "category": "furniture/electronics/appliances/decor/sports/books/clothing",
                        "confidence": 0.85,
                        "condition": "excellent/good/fair/poor",
                        "estimated_value": 50,
                        "description": "brief description of the item"
                    }
                ]
                
                Only include items that would realistically be sellable on Facebook Marketplace or similar platforms.
                Be specific with item names (e.g., "office chair" not just "chair").
                Estimate realistic prices in USD.
                """
                
                response = self.client.chat.completions.create(
                    model="Qwen/Qwen2-VL-72B-Instruct",
                    max_tokens=1024,
                    temperature=0.3,
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
                                        "url": f"data:image/jpeg;base64,{frame_info['frame_data']}"
                                    }
                                }
                            ]
                        }
                    ]
                )
                
                ai_response = response.choices[0].message.content
                print(f"AI response for frame {frame_info['id']}: {ai_response[:200]}...")
                
                try:
                    # Parse JSON response
                    start_idx = ai_response.find('[')
                    end_idx = ai_response.rfind(']') + 1
                    if start_idx != -1 and end_idx != 0:
                        json_str = ai_response[start_idx:end_idx]
                        items = json.loads(json_str)
                        
                        for item in items:
                            detected_objects.append({
                                'timestamp': frame_info['timestamp'],
                                'frame_id': frame_info['id'],
                                'frame_data': frame_info['frame_data'],
                                'object_name': item.get('object_name', 'unknown'),
                                'category': item.get('category', 'misc'),
                                'confidence': float(item.get('confidence', 0.8)),
                                'condition': item.get('condition', 'good'),
                                'estimated_value': float(item.get('estimated_value', 50)),
                                'description': item.get('description', ''),
                                'ai_response': ai_response
                            })
                            
                except json.JSONDecodeError as e:
                    print(f"JSON parsing error: {e}")
                    # Fallback: try to extract items from text
                    self._extract_items_from_text(ai_response, frame_info, detected_objects)
                
            except Exception as e:
                print(f"Error detecting objects in frame {frame_info['id']}: {str(e)}")
                continue
        
        print(f"Detected {len(detected_objects)} objects across all frames")
        return detected_objects
    
    def _extract_items_from_text(self, text: str, frame_info: Dict, detected_objects: List[Dict]):
        """Fallback method to extract items from AI response text"""
        
        # Simple fallback - look for common item keywords
        common_items = ['chair', 'table', 'lamp', 'tv', 'laptop', 'book', 'sofa', 'bed']
        
        for item in common_items:
            if item.lower() in text.lower():
                detected_objects.append({
                    'timestamp': frame_info['timestamp'],
                    'frame_id': frame_info['id'],
                    'frame_data': frame_info['frame_data'],
                    'object_name': item,
                    'category': self._get_category_for_item(item),
                    'confidence': 0.7,
                    'condition': 'good',
                    'estimated_value': self._estimate_price(item, self._get_category_for_item(item)),
                    'description': f"A {item} visible in the room",
                    'ai_response': text
                })
                break  # Only add one item per frame as fallback
    
    def _get_category_for_item(self, item_name: str) -> str:
        """Get category for an item name"""
        for category, items in self.sellable_categories.items():
            if any(item_name.lower() in item.lower() or item.lower() in item_name.lower() for item in items):
                return category
        return 'misc'
    
    def _estimate_price(self, item_name: str, category: str) -> float:
        """Estimate price for an item based on category and type"""
        
        price_ranges = {
            'furniture': {'chair': (20, 100), 'table': (50, 200), 'sofa': (100, 500), 'bed': (100, 400)},
            'electronics': {'tv': (100, 800), 'laptop': (200, 1000), 'monitor': (100, 400)},
            'appliances': {'microwave': (30, 150), 'toaster': (15, 80), 'blender': (25, 120)},
            'decor': {'lamp': (15, 80), 'mirror': (20, 100), 'vase': (10, 50)},
            'sports': {'bicycle': (50, 300), 'exercise equipment': (30, 200)},
            'books': {'book': (2, 20), 'magazine': (1, 5)},
            'clothing': {'jacket': (15, 100), 'shoes': (20, 150), 'bag': (10, 80)}
        }
        
        if category in price_ranges and item_name in price_ranges[category]:
            min_price, max_price = price_ranges[category][item_name]
            import random
            return round(random.uniform(min_price, max_price), 2)
        
        # Default price range
        return round(random.uniform(10, 100), 2)
    
    def get_category_suggestions(self) -> Dict[str, List[str]]:
        """Get category suggestions for manual item entry"""
        return self.sellable_categories
    
    async def filter_sellable_items(self, detected_objects: List[Dict]) -> List[Dict]:
        """Filter and deduplicate sellable items"""
        
        # Group similar items and remove duplicates
        unique_items = {}
        
        for obj in detected_objects:
            item_key = f"{obj['object_name']}_{obj['category']}"
            
            # Keep the one with highest confidence
            if item_key not in unique_items or obj['confidence'] > unique_items[item_key]['confidence']:
                unique_items[item_key] = {
                    'id': f"item_{len(unique_items)}",
                    'name': obj['object_name'],
                    'category': obj['category'],
                    'timestamp': obj['timestamp'],
                    'frame_id': obj['frame_id'],
                    'frame_data': obj['frame_data'],
                    'confidence': obj['confidence'],
                    'estimated_price': obj['estimated_value'],
                    'condition': obj.get('condition', 'good'),
                    'description': obj.get('description', f"A {obj['object_name']} in {obj.get('condition', 'good')} condition"),
                    'ai_response': obj.get('ai_response', '')
                }
        
        sellable_items = list(unique_items.values())
        print(f"Found {len(sellable_items)} unique sellable items")
        
        return sellable_items
