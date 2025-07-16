# SmartScape Implementation Plan

## Frontend Architecture (React + TypeScript)

### 1. Application Layout
```tsx
// Root application component
<SmartScapeApp>
  <Header />
  <ModeSelector active="design|sell" /> {/* Renamed for clarity */}
  <BuyMode /> | <SellMode /> {/* Renamed for clarity */}
</SmartScapeApp>
```

### 2. Buy Mode Components
```tsx
<BuyMode>
  <ImageUploader onUpload={analyzeRoom} />
  <RoomAnalysis results={analysis} />
  <ProductSuggestions products={suggestions} />
  <ProductCard onBuy={simulatePurchase} />
  <PurchaseConfirmation />
</BuyMode>
```

### 3. Sell Mode Components  
```tsx
<SellMode>
  <VideoUploader onUpload={extractItems} />
  <ItemExtraction progress={extractionStatus} />
  <GeneratedListings items={listings} />
  <ListingCard onPublish={createStorefront} />
  <StorefrontPreview />
  <ShareableLinks />
</SellMode>
```

## Backend API Endpoints using FastAPI

### 5. Buy Mode APIs
```python
POST /api/buy/analyze-room
# Upload image → Nebius Vision Model analysis
# Returns: room improvement suggestions

POST /api/buy/search-products  
# Send suggestions → Tavily search + scrape links
# Returns: product cards with images, prices, descriptions

POST /api/buy/purchase
# Simulate purchase → Make.com webhook
# Returns: confirmation + delivery tracking
```

### 6. Sell Mode APIs
```python
POST /api/sell/upload-video
# Upload video → OpenCV object recognition + timestamps
# Returns: extraction job ID

GET /api/sell/extraction-status/{job_id}
# Check extraction progress
# Returns: status + extracted items with timestamps

POST /api/sell/post-to-marketplace
# Auto-post to FB Marketplace with images + descriptions
# Set starting price + minimum price
# Returns: marketplace listing URLs

POST /api/sell/handle-inquiry
# AI responds to marketplace messages
# Negotiate within price range
# Returns: conversation status

POST /api/sell/schedule-meetup
# Agreement reached → Make.com calendar + email
# Returns: meeting confirmation
```

### 7. AI Agent Integration
```python
class NebiusVisionAgent:
    def analyze_room_image(self, image_data)
    def recognize_objects_in_video(self, video_frames)

class TavilyAgent:
    def search_products(self, suggestions)
    def scrape_product_links(self, search_results)

class MarketplaceAgent:
    def post_to_fb_marketplace(self, item_data)
    def respond_to_inquiries(self, message, price_range)
    def negotiate_price(self, offer, min_price)

class SchedulerAgent:
    def schedule_meetup(self, agreement_details)
```

### 8. External Service Integrations
```python
# Nebius AI Studio for vision models
# Tavily API for product search + scraping
# FB Marketplace API/automation for posting
# Make.com for calendar + email automation
# Mem0 for conversation memory
# OpenCV for video processing
```

## Implementation Steps

### Phase 1: Frontend Foundation
1. Set up React app with TypeScript
2. Create basic layout and mode switcher
3. Implement file upload components
4. Add Tailwind CSS styling

### Phase 2: Buy Mode
1. Build image upload and preview
2. Create product suggestion cards
3. Implement purchase simulation UI
4. Add confirmation and tracking views

### Phase 3: Sell Mode  
1. Build video upload with progress
2. Create item extraction visualization
3. Implement listing generation UI
4. Add negotiation chat interface

### Phase 4: Backend APIs
1. Set up FastAPI with file handling
2. Integrate Gemini Flash for image analysis
3. Connect Tavily for product search
4. Implement DeepSeek V3 for listings

### Phase 5: AI Agents & Automation
1. Build OpenCV video processing
2. Set up Supabase image storage
3. Connect Make.com webhooks
4. Integrate Mem0 for memory

### Phase 6: Storefront & Payments
1. Create mini storefront generator
2. Integrate Stripe for payments
3. Add shareable listing URLs
4. Polish UX with animations