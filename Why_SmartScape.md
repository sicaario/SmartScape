# SmartScape Implementation Guide

---

## 1. AI Pipelines — What AI is used where and how?

### Buy Mode:
- The user uploads a photo of their room.
- Nebius Vision (Gemini Flash) processes the image to understand the room layout.
- It detects things like lighting, object placement, empty wall space, etc.
- Output: a list of suggestions like “add a lamp in the corner” or “replace your chair.”

### Sell Mode:
- User uploads a walkthrough video of their room.
- OpenCV (computer vision library) breaks this video into frames.
- It extracts clear images of items at specific timestamps.
- For example: “Chair detected at 00:03, Bed at 00:07.”
- Nebius + DeepSeek V3 is then used to:
  - Analyze each item’s image
  - Automatically generate a title, price, and description for each item
- UseThis student rental marketplace for automated posting.

> You don’t need to manually describe items. The AI writes product listings automatically, similar to how eBay sellers do it manually.

---

## 2. API Flow — What do the backend endpoints do?

Think of each API as a specific job in a workflow.

### Buy Mode APIs
- `POST /api/buy/analyze-room`: Accepts image → returns room improvement ideas.
- `POST /api/buy/search-products`: Takes those ideas → uses Tavily to find real products.
- `POST /api/buy/purchase`: Simulates a purchase → triggers Make.com to send confirmation.

### Sell Mode APIs
- `POST /api/sell/upload-video`: Uploads video → starts extraction process.
- `GET /api/sell/extraction-status/{job_id}`: Lets frontend ask, “Is video processing done?”
- `POST /api/sell/post-to-marketplace`: Publishes listings to Facebook/eBay.
- `POST /api/sell/handle-inquiry`: Responds to buyer messages using AI chat.
- `POST /api/sell/schedule-meetup`: Finalizes pickup/delivery via Make.com (calendar).

> Every step in both modes is its own endpoint for modularity, which makes the system easier to scale and debug.

---

## 3. Error Handling — How does it recover from failures?

### Frontend checks:
- Prevents uploading wrong file types (e.g., .txt instead of .jpg or .mp4)
- Shows user errors like “video too large” or “upload failed”

### Backend checks:
- Try-catch blocks catch issues in AI models or file processing
- If an external service (like Tavily or Make.com) fails, it retries the request or returns a meaningful error (e.g., 503 Service Unavailable)
- Status codes (e.g., 400, 500) are used to inform frontend how to handle failure

> Example: If Tavily fails to return products, the system might show “Try again later” instead of crashing.

---

## 4. Security — How is the app secured?

- API Keys for services like Tavily, Nebius, Mem0 are stored in a `.env` file (not pushed to GitHub)
- File sanitization: Uploaded files are checked to prevent harmful code or invalid formats.
- User isolation (optional): With Appwrite or Supabase, user data can be tied to unique user IDs.
- Future upgrades can add auth tokens for private item listings or chat logs.

---

## 5. State Management — How is data stored and moved around?

### Frontend (React):
- Maintains UI state like which mode is active (Buy or Sell), upload progress, search results, etc.
- Controlled via component props/state/hooks.

### Backend (FastAPI):
- Stateless: does not store session data by default.
- Uses Mem0 to store user preferences (e.g., items they've saved or styles they prefer).
- Supabase/Appwrite handle file storage and saved product/item data.

---

## 6. Concurrency — What happens when multiple users upload at once?

- Sell mode jobs (video analysis) are asynchronous:
  - When a video is uploaded, backend starts a background task
  - The user gets a `job_id`
  - Frontend polls `GET /api/sell/extraction-status/{job_id}` to check progress

> This avoids blocking the server and allows multiple users to upload videos simultaneously.

---

## 7. Scalability — Can this system support more users or requests?

Yes. It’s designed to scale because:
- Frontend is static (React/Vite) and can be hosted on any CDN.
- Backend is API-based (FastAPI) and can be containerized (Docker) and run on multiple instances.
- Each AI agent (e.g., product search, vision model) can be turned into a microservice with its own resources.
- Storage is offloaded to Supabase (for media files) and Mem0 (for memory).

> Example: You could scale OpenCV processing separately on GPU instances while keeping FastAPI lightweight.

---

## 8. Business Case — Why does this app matter?

- For homeowners/renters: Instantly get design suggestions based on their real room without hiring a designer.
- For sellers: Create marketplace listings from a simple video — no need to take photos, write descriptions, or chat manually.
- For platforms: It encourages recycling, resale, and efficient use of space and assets.

> It saves time, reduces effort, and introduces automation in a traditionally manual domain.

---

## 9. User Memory — Why use Mem0?

Mem0 remembers:
- What products a user saved or liked
- Their preferred decor style
- Previous conversations with the chat agent

This means:
- Product suggestions improve over time
- AI responses in Sell Mode can refer back to past messages ("Last time you listed a chair for ₹1,500")

> It enables personalization across sessions, like Amazon recommending products based on past behavior.

---

## 10. Alternatives — Why these tools?

| Tool      | Why it was used                                                                 |
|-----------|----------------------------------------------------------------------------------|
| Tavily    | Real-time product search and scraping. More accurate than Google API or dummy DB.|
| Nebius    | Supports Gemini Flash and DeepSeek V3 models for advanced image/video analysis. |
| OpenCV    | Lightweight, open-source vision library that extracts image frames from video.  |
| Make.com  | No-code automation tool for email + calendar events, faster than building custom flows. |
| Mem0      | Purpose-built for memory across conversations and sessions.                     |

## 11. Why Nebius + DeepSeek V3?

Nebius = Vision Understanding:
- Acts as the "eyes" of the system.
- It processes the item image extracted from video (via OpenCV) and outputs an internal representation that captures visual meaning.
  
DeepSeek V3 = Language Generation:
- Acts as the "brain + mouth".
- It takes Nebius's vision output and translates it into:
- A product title like "Modern Wooden Coffee Table"
> A compelling description like "Minimalist design, sturdy legs, perfect for small living rooms."
Suggested price ranges, condition, or even hashtags for marketplace SEO

Why not just one model?
- Vision-only models (like Nebius) can detect and classify, but can’t write natural language descriptions.
- Language-only models (like ChatGPT) need structured vision input to write contextually.
- DeepSeek V3 is a multimodal model, but it performs best when fed with clean visual features — which Nebius provides.

> We use Nebius to deeply understand the visual content of each item — its type, condition, and features. Then, DeepSeek V3 takes this understanding and generates rich, marketplace-ready listings automatically. This combo ensures high-quality, human-like descriptions without manual input.









