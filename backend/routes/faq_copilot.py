from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import config
from typing import Dict, List, Any
import json

router = APIRouter(prefix="/api/faq-copilot", tags=["faq_copilot"])

FAQ_KNOWLEDGE = {
    "what_is_SmartScape": "SmartScape is your AI-powered home concierge that helps you transform your space! We offer two main services: Buy mode (get AI suggestions to make your room cozy) and Sell mode (identify items to declutter and sell).",
    "how_it_works": "Simply choose Buy mode to upload a room photo for decoration suggestions, or Sell mode to upload a video and identify sellable items. Our AI analyzes your space and provides personalized recommendations!",
    "pricing": "Yes! SmartScape is completely free to use. You can analyze rooms, get suggestions, and save items without any cost.",
    "uploads": "For Buy mode, upload photos of your rooms (PNG, JPG up to 10MB). For Sell mode, upload videos of your space to identify sellable items.",
    "accuracy": "Our AI is trained on thousands of interior design examples and uses advanced computer vision. While suggestions are personalized and helpful, final decisions are always yours!",
    "saving": "Absolutely! You can save any product recommendations to your saved items list and access them anytime.",
    "privacy": "We respect your privacy. Uploaded images and videos are processed securely and used only to provide you with personalized suggestions.",
    "support": "Need help? You can ask questions through our FAQ chat, or contact our support team through the website. We're here to help make your space amazing!"
}

@router.post("/")
async def faq_copilot_runtime(request: Request):
    """FAQ CopilotKit runtime endpoint"""
    
    try:
        body = await request.json()
        
        # Handle different CopilotKit request types
        if "messages" in body:
            # Chat completion request
            messages = body.get("messages", [])
            
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
            
            # Generate FAQ response
            response = generate_faq_response(latest_message)
            
            # Return in OpenAI-compatible format
            return JSONResponse(content={
                "id": "chatcmpl-faq-" + str(hash(latest_message))[:8],
                "object": "chat.completion",
                "created": 1234567890,
                "model": "SmartScape-faq-assistant",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(latest_message.split()),
                    "completion_tokens": len(response.split()),
                    "total_tokens": len(latest_message.split()) + len(response.split())
                }
            })
        
        else:
            # Other CopilotKit requests
            return JSONResponse(content={"status": "ok"})
        
    except Exception as e:
        print(f"Error in FAQ copilot runtime: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in FAQ copilot runtime: {str(e)}")

def generate_faq_response(message: str) -> str:
    """Generate FAQ response based on user message"""
    
    message_lower = message.lower()
    
    # Check for specific keywords and provide relevant responses
    if any(word in message_lower for word in ["what is", "what's", "about SmartScape", "explain"]):
        return FAQ_KNOWLEDGE["what_is_SmartScape"]
    
    elif any(word in message_lower for word in ["how does", "how it works", "how to use"]):
        return FAQ_KNOWLEDGE["how_it_works"]
    
    elif any(word in message_lower for word in ["free", "cost", "price", "pricing", "money"]):
        return FAQ_KNOWLEDGE["pricing"]
    
    elif any(word in message_lower for word in ["upload", "file", "photo", "video", "image"]):
        return FAQ_KNOWLEDGE["uploads"]
    
    elif any(word in message_lower for word in ["accurate", "accuracy", "reliable", "good"]):
        return FAQ_KNOWLEDGE["accuracy"]
    
    elif any(word in message_lower for word in ["save", "saving", "saved", "bookmark"]):
        return FAQ_KNOWLEDGE["saving"]
    
    elif any(word in message_lower for word in ["privacy", "private", "secure", "data"]):
        return FAQ_KNOWLEDGE["privacy"]
    
    elif any(word in message_lower for word in ["help", "support", "contact", "problem"]):
        return FAQ_KNOWLEDGE["support"]
    
    else:
        # Default response with helpful suggestions
        return """I'm here to help with questions about SmartScape! Here are some things I can tell you about:

• **What is SmartScape?** - Learn about our AI-powered home concierge
• **How it works** - Understand our Buy and Sell modes
• **Pricing** - Yes, it's completely free!
• **File uploads** - What you can upload and file requirements
• **Privacy & Security** - How we protect your data
• **Getting help** - Support and contact information

What would you like to know more about?"""

@router.get("/info")
async def faq_copilot_info():
    """FAQ CopilotKit info endpoint"""
    return JSONResponse(content={
        "runtime": "SmartScape-faq-copilot",
        "version": "1.0.0",
        "capabilities": ["chat"],
        "description": "FAQ assistant for SmartScape questions"
    })
