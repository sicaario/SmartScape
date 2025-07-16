from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from services.room_analyzer import RoomAnalyzer
from services.product_search import ProductSearchService
from services.appwrite_service import AppwriteService
from services.chat_service import ChatService
from services.mem0_service import Mem0Service
import asyncio

router = APIRouter(prefix="/api/buy", tags=["buy_mode"])

# Initialize services
room_analyzer = RoomAnalyzer()
product_search = ProductSearchService()
appwrite_service = AppwriteService()
chat_service = ChatService()

# Initialize mem0 service with error handling
try:
    mem0_service = Mem0Service()
    MEM0_ENABLED = True
    print("Mem0 service enabled with debug logging")
except Exception as e:
    print(f"Warning: Mem0 service not available: {str(e)}")
    mem0_service = None
    MEM0_ENABLED = False
print("Mem0 service temporarily disabled - installation issue")

@router.post("/analyze-room")
async def analyze_room(file: UploadFile = File(...), user_id: str = "default_user"):
    """Analyze uploaded room image and provide personalized decoration suggestions"""
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Check file size (10MB limit)
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")
    
    try:
        print(f"Processing file: {file.filename}, size: {file.size}, type: {file.content_type}")
        
        # Read image data
        image_data = await file.read()
        print(f"Image data read successfully, length: {len(image_data)}")
        
        # Analyze room
        print("Starting room analysis...")
        analysis = await room_analyzer.analyze_room_image(image_data)
        print(f"Room analysis completed: {analysis.get('room_type', 'unknown')}")
        
        # Get personalized suggestions if mem0 is available
        original_suggestions = analysis['suggestions']
        if MEM0_ENABLED and mem0_service:
            try:
                personalized_suggestions = await mem0_service.get_personalized_suggestions(
                    user_id, analysis.get('room_type', 'unknown'), original_suggestions
                )
                analysis['suggestions'] = personalized_suggestions
                analysis['personalized'] = True
                
                # Store room analysis in mem0 for future personalization
                await mem0_service.store_room_analysis_preference(user_id, analysis)
                
            except Exception as e:
                print(f"Error with mem0 personalization: {str(e)}")
                analysis['personalized'] = False
        else:
            analysis['personalized'] = False
        
        # Search for products based on suggestions
        print("Starting product search...")
        products = await product_search.search_products(analysis['suggestions'])
        print(f"Product search completed, found {len(products)} products")
        
        return JSONResponse(content={
            "success": True,
            "analysis": analysis,
            "products": products,
            "message": "Room analyzed successfully! Here are some suggestions to make your space more cozy."
        })
        
    except Exception as e:
        print(f"Error in analyze_room: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@router.post("/search-product")
async def search_product(product_name: str, category: str = "", user_id: str = "default_user"):
    """Search for specific products and learn from user search behavior"""
    try:
        products = await product_search.search_specific_product(product_name, category)
        
        # Learn from search interaction
        if MEM0_ENABLED and mem0_service:
            try:
                await mem0_service.learn_from_interaction(user_id, "product_search", {
                    "query": product_name,
                    "category": category
                })
            except Exception as e:
                print(f"Error learning from search interaction: {str(e)}")
        
        return JSONResponse(content={
            "success": True,
            "products": products,
            "query": product_name
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching products: {str(e)}")

@router.get("/suggestions/{room_type}")
async def get_room_suggestions(room_type: str, user_id: str = "default_user"):
    """Get personalized suggestions for a room type"""
    
    suggestions_db = {
        "living_room": [
            {"category": "lighting", "item": "floor lamps", "description": "Create ambient lighting", "priority": "high"},
            {"category": "textiles", "item": "throw pillows", "description": "Add comfort and color", "priority": "high"},
            {"category": "plants", "item": "potted plants", "description": "Bring nature indoors", "priority": "medium"}
        ],
        "bedroom": [
            {"category": "lighting", "item": "bedside lamps", "description": "Soft reading light", "priority": "high"},
            {"category": "textiles", "item": "cozy blankets", "description": "Layer textures for warmth", "priority": "high"},
            {"category": "decor", "item": "wall art", "description": "Personalize your space", "priority": "medium"}
        ],
        "kitchen": [
            {"category": "lighting", "item": "pendant lights", "description": "Task and ambient lighting", "priority": "high"},
            {"category": "decor", "item": "herb garden", "description": "Fresh herbs and greenery", "priority": "medium"},
            {"category": "textiles", "item": "kitchen rugs", "description": "Comfort and style", "priority": "low"}
        ]
    }
    
    suggestions = suggestions_db.get(room_type, [])
    
    if not suggestions:
        raise HTTPException(status_code=404, detail="Room type not found")
    
    # Learn from room suggestion view
    if MEM0_ENABLED and mem0_service:
        try:
            await mem0_service.learn_from_interaction(user_id, "room_suggestion_view", {
                "room_type": room_type
            })
        except Exception as e:
            print(f"Error learning from room suggestion view: {str(e)}")
    
    return JSONResponse(content={
        "success": True,
        "room_type": room_type,
        "suggestions": suggestions
    })

@router.post("/save-item")
async def save_item(request_data: dict):
    """Save a product recommendation and learn user preferences"""
    
    try:
        user_id = request_data.get("user_id", "default_user")
        product_data = request_data.get("product", {})
        
        if not product_data:
            raise HTTPException(status_code=400, detail="Product data is required")
        
        # Save to Appwrite
        saved_item_id = await appwrite_service.save_buy_recommendation(user_id, product_data)
        
        # Store preference in mem0
        if MEM0_ENABLED and mem0_service:
            try:
                await mem0_service.store_saved_item_preference(user_id, product_data)
            except Exception as e:
                print(f"Error storing saved item preference: {str(e)}")
        
        return JSONResponse(content={
            "success": True,
            "saved_item_id": saved_item_id,
            "message": "Item saved successfully!"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving item: {str(e)}")

@router.get("/saved-items/{user_id}")
async def get_saved_items(user_id: str):
    """Get all saved items for a user"""
    
    try:
        saved_items = await appwrite_service.get_saved_recommendations(user_id)
        
        return JSONResponse(content={
            "success": True,
            "saved_items": saved_items,
            "count": len(saved_items)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting saved items: {str(e)}")

@router.post("/reject-suggestion")
async def reject_suggestion(request_data: dict):
    """Record rejected suggestions to improve future recommendations"""
    
    try:
        user_id = request_data.get("user_id", "default_user")
        rejected_item = request_data.get("item", {})
        reason = request_data.get("reason", "")
        
        if not rejected_item:
            raise HTTPException(status_code=400, detail="Rejected item data is required")
        
        # Store rejection in mem0
        if MEM0_ENABLED and mem0_service:
            try:
                await mem0_service.store_rejected_suggestion(user_id, rejected_item, reason)
                
                return JSONResponse(content={
                    "success": True,
                    "message": "Feedback recorded! We'll improve future suggestions."
                })
            except Exception as e:
                print(f"Error storing rejected suggestion: {str(e)}")
                raise HTTPException(status_code=500, detail="Error recording feedback")
        else:
            return JSONResponse(content={
                "success": False,
                "message": "Personalization service not available"
            })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording rejection: {str(e)}")

@router.get("/user-preferences/{user_id}")
async def get_user_preferences(user_id: str):
    """Get user preferences and personalization data"""
    
    try:
        if MEM0_ENABLED and mem0_service:
            preferences = await mem0_service.get_user_preferences(user_id)
            
            return JSONResponse(content={
                "success": True,
                "preferences": preferences,
                "personalization_enabled": True
            })
        else:
            return JSONResponse(content={
                "success": False,
                "message": "Personalization service not available",
                "personalization_enabled": False
            })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user preferences: {str(e)}")

@router.post("/chat")
async def handle_chat(request_data: dict):
    """Handle intelligent chat messages with Mem0 and Tavily"""
    
    try:
        user_id = request_data.get("user_id", "default_user")
        message = request_data.get("message", "")
        conversation_history = request_data.get("conversation_history", [])
        
        if not message.strip():
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Use intelligent chat service
        result = await chat_service.handle_chat_message(user_id, message, conversation_history)
        
        return JSONResponse(content={
            "success": True,
            "response": result["response"],
            "suggested_actions": result.get("suggested_actions", []),
            "user_preferences_used": result.get("user_preferences_used", False),
            "mem0_enabled": result.get("mem0_enabled", False)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error handling chat: {str(e)}")
