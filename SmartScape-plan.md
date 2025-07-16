SmartScape's Operational Dynamics
Buy Mode — Crafting Your Ideal Space

The user initiates a transformation by submitting an image of their room.

Our system, utilizing Gemini Flash, performs an in-depth visual assessment, identifying opportunities for aesthetic and functional improvements (e.g., optimizing lighting, reconfiguring seating).

The BuyAgent proceeds to curate highly relevant product recommendations, leveraging the expansive database of the Tavily API.

An intuitive display presents a selection of product options, complete with high-fidelity images, pricing, and descriptive text.

User confirmation of a selection triggers a simulated acquisition process.

Make.com then orchestrates the dispatch of an immediate confirmation email and schedules a hypothetical delivery event.

All transaction specifics are securely logged for recall within Mem0 and for persistent storage in Appwrite.

Sell Mode — Streamlining Asset Liquidation

The journey begins with the user uploading a video walkthrough of their space.

Gemini Flash intelligently processes this video, generating a structured inventory of potential sellable items, each precisely timestamped.

OpenCV is then employed to extract pristine, high-resolution image frames corresponding to every identified item.

These extracted visual assets are subsequently uploaded to Supabase storage for secure hosting.

Data for each item is transmitted to DeepSeek V3 (via Nebius API), which autonomously generates compelling titles, detailed descriptions, and formats the complete listing content.

The system presents the user with fully rendered listings, showcasing the actual item imagery, for final review.

Activating the "Negotiate" feature initiates a dynamic chat interface, driven by DeepSeek V3, to simulate buyer interactions and price discussions.

Mem0 diligently tracks the comprehensive history of buyer communications and the progression of negotiations.

Upon reaching an agreement, the SchedulerAgent proposes optimal pickup or delivery times.

Make.com then seamlessly integrates this scheduled event into a calendar system and dispatches automated reminders to all pertinent parties.









