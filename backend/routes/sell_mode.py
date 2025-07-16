from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from services.video_processor import VideoProcessor
from services.listing_generator import ListingGenerator
from services.marketplace_automation import MarketplaceAutomation
from services.negotiation_ai import NegotiationAI
from services.usethis_automation import UseThisAutomation
from services.appwrite_service import AppwriteService
import asyncio
import uuid
from typing import Dict, List

router = APIRouter(prefix="/api/sell", tags=["sell_mode"])

# Initialize services
video_processor = VideoProcessor()
listing_generator = ListingGenerator()
marketplace_automation = MarketplaceAutomation()
negotiation_ai = NegotiationAI()
usethis_automation = UseThisAutomation()
appwrite_service = AppwriteService()

# Store for tracking extraction jobs
extraction_jobs: Dict[str, Dict] = {}

@router.post("/upload-video")
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload video and start object extraction process"""
    
    # Validate file type
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Check file size (100MB limit)
    if file.size > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 100MB")
    
    try:
        print(f"Processing video: {file.filename}, size: {file.size}, type: {file.content_type}")
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        extraction_jobs[job_id] = {
            "status": "processing",
            "progress": 0,
            "filename": file.filename,
            "items": [],
            "error": None
        }
        
        # Read video data
        video_data = await file.read()
        
        # Start background processing
        background_tasks.add_task(process_video_extraction, job_id, video_data, file.filename)
        
        return JSONResponse(content={
            "success": True,
            "job_id": job_id,
            "message": "Video upload started. Use the job ID to check extraction status."
        })
        
    except Exception as e:
        print(f"Error in upload_video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")

@router.get("/extraction-status/{job_id}")
async def get_extraction_status(job_id: str):
    """Check the status of video extraction job"""
    
    if job_id not in extraction_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = extraction_jobs[job_id]
    
    return JSONResponse(content={
        "success": True,
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "filename": job["filename"],
        "frames": job.get("frames", []),  # Return frames for manual review
        "items": job["items"],
        "error": job.get("error")
    })

@router.post("/generate-listings")
async def generate_listings(request_data: dict):
    """Generate marketplace listings for extracted items"""
    
    job_id = request_data.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")
    
    if job_id not in extraction_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = extraction_jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Extraction not completed yet")
    
    try:
        print(f"Generating listings for {len(job['items'])} items")
        
        # Generate listings for each item
        listings = []
        for item in job["items"]:
            listing = await listing_generator.create_listing(item)
            listings.append(listing)
        
        return JSONResponse(content={
            "success": True,
            "listings": listings,
            "message": f"Generated {len(listings)} marketplace listings"
        })
        
    except Exception as e:
        print(f"Error generating listings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating listings: {str(e)}")

@router.post("/negotiate")
async def handle_negotiation(listing_id: str, buyer_message: str, current_price: float):
    """Handle buyer negotiation using AI"""
    
    try:
        response = await listing_generator.handle_negotiation(
            listing_id, buyer_message, current_price
        )
        
        return JSONResponse(content={
            "success": True,
            "response": response,
            "message": "Negotiation response generated"
        })
        
    except Exception as e:
        print(f"Error in negotiation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error handling negotiation: {str(e)}")

@router.post("/add-manual-item")
async def add_manual_item(job_id: str, frame_id: str, item_name: str, category: str, price: float, condition: str = "good"):
    """Add a manually identified item to a frame"""
    
    if job_id not in extraction_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = extraction_jobs[job_id]
    
    # Create manual item
    manual_item = {
        'id': f"manual_item_{len(job['items'])}",
        'name': item_name,
        'category': category,
        'frame_id': frame_id,
        'estimated_price': price,
        'condition': condition,
        'description': f"A {item_name} in {condition} condition",
        'timestamp': 0  # Will be updated based on frame
    }
    
    # Add to job items
    job['items'].append(manual_item)
    
    return JSONResponse(content={
        "success": True,
        "item": manual_item,
        "message": "Item added successfully"
    })

@router.get("/category-suggestions")
async def get_category_suggestions():
    """Get category suggestions for manual item entry"""
    
    video_processor = VideoProcessor()
    suggestions = video_processor.get_category_suggestions()
    
    return JSONResponse(content={
        "success": True,
        "categories": suggestions
    })

@router.put("/update-item")
async def update_item(request_data: dict):
    """Update item name and/or price"""
    
    job_id = request_data.get("job_id")
    item_index = request_data.get("item_index")
    name = request_data.get("name")
    estimated_price = request_data.get("estimated_price")
    
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")
    
    if item_index is None:
        raise HTTPException(status_code=400, detail="item_index is required")
    
    if job_id not in extraction_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = extraction_jobs[job_id]
    
    if item_index >= len(job['items']) or item_index < 0:
        raise HTTPException(status_code=400, detail="Invalid item index")
    
    # Update the item
    if name is not None:
        job['items'][item_index]['name'] = name
    if estimated_price is not None:
        job['items'][item_index]['estimated_price'] = estimated_price
    
    return JSONResponse(content={
        "success": True,
        "item": job['items'][item_index],
        "message": "Item updated successfully"
    })

@router.delete("/delete-item")
async def delete_item(request_data: dict):
    """Delete an item from the extracted items list"""
    
    job_id = request_data.get("job_id")
    item_index = request_data.get("item_index")
    
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")
    
    if item_index is None:
        raise HTTPException(status_code=400, detail="item_index is required")
    
    if job_id not in extraction_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = extraction_jobs[job_id]
    
    if item_index >= len(job['items']) or item_index < 0:
        raise HTTPException(status_code=400, detail="Invalid item index")
    
    # Remove the item
    deleted_item = job['items'].pop(item_index)
    
    return JSONResponse(content={
        "success": True,
        "deleted_item": deleted_item,
        "remaining_items": len(job['items']),
        "message": "Item deleted successfully"
    })

@router.post("/setup-facebook-login")
async def setup_facebook_login(email: str, password: str):
    """Setup Facebook login for marketplace automation"""
    
    try:
        success = marketplace_automation.login_to_facebook(email, password)
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": "Facebook login successful. Ready to post listings."
            })
        else:
            raise HTTPException(status_code=400, detail="Facebook login failed")
            
    except Exception as e:
        print(f"Error setting up Facebook login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error setting up Facebook login: {str(e)}")

@router.post("/post-to-facebook")
async def post_to_facebook(listing_data: dict):
    """Automatically post listing to Facebook Marketplace"""
    
    try:
        success = marketplace_automation.post_to_marketplace(listing_data)
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": "Listing posted to Facebook Marketplace successfully"
            })
        else:
            raise HTTPException(status_code=400, detail="Failed to post to Facebook Marketplace")
            
    except Exception as e:
        print(f"Error posting to Facebook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error posting to Facebook: {str(e)}")

@router.post("/handle-buyer-message")
async def handle_buyer_message(listing_id: str, buyer_message: str, listing_data: dict):
    """Handle buyer message with AI negotiation"""
    
    try:
        # Get conversation history
        conversation_history = negotiation_ai.get_conversation_history(listing_id)
        
        # Generate AI response
        response = negotiation_ai.handle_buyer_message(
            listing_id, buyer_message, listing_data, conversation_history
        )
        
        return JSONResponse(content={
            "success": True,
            "ai_response": response["ai_response"],
            "action": response["action"],
            "suggested_price": response.get("suggested_price"),
            "next_steps": response["next_steps"],
            "conversation_history": response["conversation_history"]
        })
        
    except Exception as e:
        print(f"Error handling buyer message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error handling buyer message: {str(e)}")

@router.post("/suggest-meetup")
async def suggest_meetup(listing_id: str, buyer_message: str):
    """Suggest meetup times for item pickup"""
    
    try:
        suggestion = negotiation_ai.suggest_meetup_time(buyer_message)
        
        return JSONResponse(content={
            "success": True,
            "suggested_times": suggestion["suggested_times"],
            "message": suggestion["message"]
        })
        
    except Exception as e:
        print(f"Error suggesting meetup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error suggesting meetup: {str(e)}")

@router.get("/conversation-history/{listing_id}")
async def get_conversation_history(listing_id: str):
    """Get conversation history for a listing"""
    
    try:
        history = negotiation_ai.get_conversation_history(listing_id)
        
        return JSONResponse(content={
            "success": True,
            "conversation_history": history
        })
        
    except Exception as e:
        print(f"Error getting conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting conversation history: {str(e)}")

@router.post("/setup-usethis-login")
async def setup_usethis_login(email: str, password: str = None):
    """Setup UseThis login for marketplace automation"""
    
    try:
        success = usethis_automation.login_to_usethis(email, password)
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": "UseThis login successful. Ready to post listings."
            })
        else:
            raise HTTPException(status_code=400, detail="UseThis login failed")
            
    except Exception as e:
        print(f"Error setting up UseThis login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error setting up UseThis login: {str(e)}")

@router.post("/post-to-usethis")
async def post_to_usethis(request_data: dict):
    """Automatically post listings to UseThis rental marketplace"""
    
    job_id = request_data.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")
    
    if job_id not in extraction_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = extraction_jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Extraction not completed yet")
    
    try:
        posted_listings = []
        failed_listings = []
        
        for item in job["items"]:
            # Convert item to UseThis listing format
            listing_data = {
                "title": f"{item['name'].title()} - Available for Rent",
                "description": f"Rent this {item['name']} in {item.get('condition', 'good')} condition. Perfect for students who need it temporarily! Original value: ${item['estimated_price']}",
                "price": float(item['estimated_price']),
                "category": item.get('category', 'misc'),
                "condition": item.get('condition', 'good'),
                "image_data": item.get('frame_data', ''),
                "rental_type": "daily"
            }
            
            # Post to UseThis
            success = usethis_automation.post_to_usethis(listing_data)
            
            if success:
                posted_listings.append({
                    "item_name": item['name'],
                    "title": listing_data['title'],
                    "rental_price": max(1, round(item['estimated_price'] / 30, 2)),
                    "status": "posted"
                })
            else:
                failed_listings.append({
                    "item_name": item['name'],
                    "error": "Failed to post"
                })
        
        return JSONResponse(content={
            "success": True,
            "posted_count": len(posted_listings),
            "failed_count": len(failed_listings),
            "posted_listings": posted_listings,
            "failed_listings": failed_listings,
            "platform_url": "https://use-this.netlify.app",
            "message": f"Posted {len(posted_listings)} items to UseThis rental marketplace!"
        })
        
    except Exception as e:
        print(f"Error posting to UseThis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error posting to UseThis: {str(e)}")

@router.get("/usethis-listings")
async def get_usethis_listings():
    """Get current listings from UseThis platform"""
    
    try:
        listings = usethis_automation.get_posted_listings()
        
        return JSONResponse(content={
            "success": True,
            "listings": listings,
            "platform_url": "https://use-this.netlify.app"
        })
        
    except Exception as e:
        print(f"Error getting UseThis listings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting UseThis listings: {str(e)}")

@router.post("/create-storefront")
async def create_storefront(request_data: dict):
    """Generate fake UseThis rental marketplace data using Nebius AI"""
    
    job_id = request_data.get("job_id")
    email = request_data.get("email")
    password = request_data.get("password", "")
    
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")
    
    if not email:
        raise HTTPException(status_code=400, detail="UseThis email is required")
    
    if job_id not in extraction_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = extraction_jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Extraction not completed yet")
    
    try:
        # Generate fake UseThis listings using AI
        posted_listings = []
        failed_listings = []
        
        for item in job["items"]:
            try:
                # Upload image to Appwrite storage
                image_url = await appwrite_service.upload_image_to_storage_only(
                    image_data=item.get('frame_data', ''),
                    filename=f"{item['name']}_usethis.jpg"
                )
                
                # Use AI to generate realistic rental listing data
                listing_data = await generate_usethis_listing_with_ai(item)
                
                # Simulate successful posting (fake data)
                rental_price = max(1, round(item['estimated_price'] / 30, 2))
                posted_listings.append({
                    "id": item.get("id", str(uuid.uuid4())[:8]),
                    "title": listing_data['title'],
                    "description": listing_data['description'],
                    "original_price": float(item['estimated_price']),
                    "rental_price": rental_price,
                    "category": item.get('category', 'misc'),
                    "condition": item.get('condition', 'good'),
                    "image_url": image_url,  # Use Appwrite storage URL
                    "status": "live",
                    "platform": "UseThis",
                    "views": listing_data.get('views', 0),
                    "inquiries": listing_data.get('inquiries', 0)
                })
                
            except Exception as e:
                print(f"Error processing item '{item['name']}': {str(e)}")
                failed_listings.append({
                    "item_name": item['name'],
                    "error": str(e)
                })
        
        # Generate success response with fake analytics
        return JSONResponse(content={
            "success": True,
            "platform": "UseThis",
            "platform_url": "https://use-this.netlify.app",
            "posted_count": len(posted_listings),
            "failed_count": len(failed_listings),
            "listings": posted_listings,
            "failed_listings": failed_listings,
            "total_potential_income": sum(listing["rental_price"] * 30 for listing in posted_listings),
            "message": f"🎉 Posted {len(posted_listings)} items to UseThis rental marketplace!",
            "next_steps": [
                "Visit UseThis to manage your listings",
                "Respond to rental requests from students", 
                "Set availability and pickup times",
                "Earn money from your unused items!"
            ]
        })
        
    except Exception as e:
        print(f"Error generating UseThis data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating UseThis data: {str(e)}")

@router.get("/storefront/{storefront_id}")
async def get_storefront(storefront_id: str):
    """Get storefront details (redirects to UseThis)"""
    
    return JSONResponse(content={
        "success": True,
        "storefront_id": storefront_id,
        "redirect_url": "https://use-this.netlify.app",
        "message": "Redirecting to UseThis platform"
    })

@router.get("/conversation-history/{listing_id}")
async def get_conversation_history(listing_id: str):
    """Get conversation history for a listing"""
    
    try:
        history = negotiation_ai.get_conversation_history(listing_id)
        
        return JSONResponse(content={
            "success": True,
            "conversation_history": history
        })
        
    except Exception as e:
        print(f"Error getting conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting conversation history: {str(e)}")

@router.post("/post-to-ebay")
async def post_to_ebay(request_data: dict):
    """Post listings to eBay using official API"""
    
    job_id = request_data.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")
    
    if job_id not in extraction_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = extraction_jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Extraction not completed yet")
    
    try:
        posted_listings = []
        failed_listings = []
        
        for item in job["items"]:
            try:
                # Create eBay listing
                result = await ebay_service.create_listing(item)
                
                if result["success"]:
                    posted_listings.append({
                        "item_name": item['name'],
                        "sku": result["sku"],
                        "offer_id": result["offer_id"],
                        "price": item['estimated_price'],
                        "status": "listed",
                        "marketplace": "eBay",
                        "sandbox": result.get("sandbox", True)
                    })
                else:
                    failed_listings.append({
                        "item_name": item['name'],
                        "error": result["error"]
                    })
                    
            except Exception as e:
                failed_listings.append({
                    "item_name": item['name'],
                    "error": str(e)
                })
        
        return JSONResponse(content={
            "success": True,
            "platform": "eBay",
            "sandbox_mode": ebay_service.sandbox,
            "posted_count": len(posted_listings),
            "failed_count": len(failed_listings),
            "listings": posted_listings,
            "failed_listings": failed_listings,
            "message": f"🎉 Posted {len(posted_listings)} items to eBay{'(Sandbox)' if ebay_service.sandbox else ''}!",
            "next_steps": [
                "Monitor your eBay seller dashboard",
                "Respond to buyer questions",
                "Manage inventory and pricing",
                "Track sales and shipping"
            ]
        })
        
    except Exception as e:
        print(f"Error posting to eBay: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error posting to eBay: {str(e)}")

@router.get("/ebay-listing-status/{offer_id}")
async def get_ebay_listing_status(offer_id: str):
    """Get eBay listing status"""
    
    try:
        status = await ebay_service.get_listing_status(offer_id)
        
        return JSONResponse(content={
            "success": True,
            "status": status
        })
        
    except Exception as e:
        print(f"Error getting eBay listing status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting eBay listing status: {str(e)}")

@router.get("/ebay-config")
async def get_ebay_config():
    """Get eBay service configuration status"""
    
    return JSONResponse(content={
        "success": True,
        "enabled": ebay_service.enabled,
        "sandbox": ebay_service.sandbox,
        "app_id_configured": bool(ebay_service.app_id),
        "cert_id_configured": bool(ebay_service.cert_id),
        "dev_id_configured": bool(ebay_service.dev_id),
        "auth_token_configured": bool(ebay_service.sandbox_auth_token)
    })

async def process_video_extraction(job_id: str, video_data: bytes, filename: str):
    """Background task to process video and extract sellable items using AI"""
    
    try:
        # Update progress
        extraction_jobs[job_id]["progress"] = 10
        
        # Extract frames from video
        frames = await video_processor.extract_frames(video_data)
        extraction_jobs[job_id]["progress"] = 30
        extraction_jobs[job_id]["frames"] = frames
        
        # Detect objects in frames using AI
        detected_objects = await video_processor.detect_objects(frames)
        extraction_jobs[job_id]["progress"] = 60
        
        # Filter for sellable items
        sellable_items = await video_processor.filter_sellable_items(detected_objects)
        extraction_jobs[job_id]["progress"] = 80
        
        # Save items to Appwrite database
        user_id = "default_user"  # You can get this from session/auth
        
        for item in sellable_items:
            try:
                # Upload image to Appwrite
                image_url = await appwrite_service.upload_image(
                    image_data=item["frame_data"],
                    user_id=user_id,
                    image_type="item_frame",
                    original_filename=f"{item['name']}_frame.jpg"
                )
                
                # Save item to database
                item_doc_id = await appwrite_service.save_extracted_item(
                    item=item,
                    user_id=user_id,
                    image_url=image_url
                )
                
                # Update item with database info
                item["appwrite_doc_id"] = item_doc_id
                item["image_url"] = image_url
                
                print(f"Saved item '{item['name']}' to Appwrite with image URL: {image_url}")
                
            except Exception as e:
                print(f"Error saving item '{item['name']}' to Appwrite: {str(e)}")
                # Continue with other items even if one fails
                continue
        
        # Store results
        extraction_jobs[job_id]["items"] = sellable_items
        extraction_jobs[job_id]["progress"] = 100
        extraction_jobs[job_id]["status"] = "completed"
        
        print(f"Video extraction completed for job {job_id}: {len(sellable_items)} items found and saved to Appwrite")
        
    except Exception as e:
        print(f"Error in video extraction for job {job_id}: {str(e)}")
        extraction_jobs[job_id]["status"] = "failed"
        extraction_jobs[job_id]["error"] = str(e)

async def generate_usethis_listing_with_ai(item: Dict) -> Dict:
    """Generate UseThis rental listing data using Nebius AI"""
    
    try:
        from openai import OpenAI
        import config
        import random
        
        client = OpenAI(
            base_url="https://api.studio.nebius.ai/v1/",
            api_key=config.NEBIUS_API_KEY
        )
        
        prompt = f"""
        Generate a rental listing for UseThis student marketplace for this item:
        
        Item: {item['name']}
        Category: {item['category']}
        Original Price: ${item['estimated_price']}
        Condition: {item.get('condition', 'good')}
        
        Create a JSON response:
        {{
            "title": "Student-friendly rental title (max 60 chars)",
            "description": "Description emphasizing rental benefits for students (max 200 chars)",
            "rental_price_per_day": "daily rental price (original price / 30)",
            "views": "random number 5-50",
            "inquiries": "random number 0-8"
        }}
        
        Make it appealing to college students who need temporary access to items.
        Focus on convenience, affordability, and short-term rental benefits.
        """
        
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",
            max_tokens=512,
            temperature=0.3,
            top_p=0.95,
            messages=[{"role": "user", "content": prompt}]
        )
        
        ai_response = response.choices[0].message.content
        
        try:
            import json
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = ai_response[start_idx:end_idx]
                result = json.loads(json_str)
            else:
                raise json.JSONDecodeError("No JSON found", "", 0)
        except json.JSONDecodeError:
            # Fallback with realistic fake data
            result = {
                "title": f"{item['name'].title()} - Student Rental",
                "description": f"Rent this {item['name']} perfect for students! Daily rental available.",
                "rental_price_per_day": max(1, round(item['estimated_price'] / 30, 2)),
                "views": random.randint(5, 50),
                "inquiries": random.randint(0, 8)
            }
        
        return {
            "title": result.get("title", f"{item['name'].title()} - Student Rental"),
            "description": result.get("description", f"Rent this {item['name']} perfect for students!"),
            "views": int(result.get("views", random.randint(5, 50))),
            "inquiries": int(result.get("inquiries", random.randint(0, 8)))
        }
        
    except Exception as e:
        print(f"Error generating AI listing: {str(e)}")
        # Return fallback data
        import random
        return {
            "title": f"{item['name'].title()} - Student Rental",
            "description": f"Rent this {item['name']} perfect for students! Daily rental available.",
            "views": random.randint(5, 50),
            "inquiries": random.randint(0, 8)
        }
