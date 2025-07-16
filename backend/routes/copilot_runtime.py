from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import config
from services.chat_service import ChatService
from services.product_search import ProductSearchService
from typing import Dict, List, Any
import json

router = APIRouter(prefix="/api/copilot", tags=["copilot"])

# Initialize services
chat_service = ChatService()
product_search = ProductSearchService()

@router.post("/")
async def copilot_runtime(request: Request):
    """Main CopilotKit runtime endpoint"""
    
    try:
        body = await request.json()
        
        # Handle different CopilotKit request types
        if "messages" in body:
            # Chat completion request
            messages = body.get("messages", [])
            user_id = body.get("user_id", "default_user")
            
            if not messages:
                raise HTTPException(status_code=400, detail="Messages are required")
            
            # Get the latest user message
            latest_message = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    latest_message = msg.get("content", "")
                    break
            
            if not latest_message:
                raise HTTPException(status_code=400, detail="No user message found")
            
            # Handle the chat message
            result = await chat_service.handle_chat_message(user_id, latest_message, messages)
            
            # Return in OpenAI-compatible format
            return JSONResponse(content={
                "id": "chatcmpl-" + str(hash(latest_message))[:8],
                "object": "chat.completion",
                "created": 1234567890,
                "model": "SmartScape-assistant",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result["response"]
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(latest_message.split()),
                    "completion_tokens": len(result["response"].split()),
                    "total_tokens": len(latest_message.split()) + len(result["response"].split())
                }
            })
        
        else:
            # Other CopilotKit requests
            return JSONResponse(content={"status": "ok"})
        
    except Exception as e:
        print(f"Error in copilot runtime: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in copilot runtime: {str(e)}")

@router.get("/info")
async def copilot_info():
    """CopilotKit info endpoint"""
    return JSONResponse(content={
        "runtime": "SmartScape-copilot",
        "version": "1.0.0",
        "capabilities": ["chat", "actions"],
        "actions": [
            {
                "name": "search_products",
                "description": "Search for home decor products",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Product search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
    })

@router.post("/chat")
async def copilot_chat(request_data: dict):
    """CopilotKit chat endpoint"""
    
    try:
        messages = request_data.get("messages", [])
        user_id = request_data.get("user_id", "default_user")
        
        if not messages:
            raise HTTPException(status_code=400, detail="Messages are required")
        
        # Get the latest user message
        latest_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                latest_message = msg.get("content", "")
                break
        
        if not latest_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        # Handle the chat message
        result = await chat_service.handle_chat_message(user_id, latest_message, messages)
        
        return JSONResponse(content={
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": result["response"]
                }
            }],
            "suggested_actions": result.get("suggested_actions", []),
            "user_preferences_used": result.get("user_preferences_used", False)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in copilot chat: {str(e)}")

@router.post("/actions/search_products")
async def search_products_action(request_data: dict):
    """CopilotKit action for searching products"""
    
    try:
        query = request_data.get("query", "")
        user_id = request_data.get("user_id", "default_user")
        
        if not query:
            raise HTTPException(status_code=400, detail="Search query is required")
        
        result = await chat_service.search_products_for_chat(user_id, query)
        
        return JSONResponse(content={
            "success": result["success"],
            "products": result["products"],
            "message": f"Found {len(result['products'])} products for '{query}'"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching products: {str(e)}")

@router.get("/actions")
async def get_available_actions():
    """Get available CopilotKit actions"""
    
    return JSONResponse(content={
        "actions": [
            {
                "name": "search_products",
                "description": "Search for home decor products",
                "parameters": [
                    {
                        "name": "query",
                        "type": "string",
                        "description": "Product search query",
                        "required": True
                    }
                ]
            }
        ]
    })
