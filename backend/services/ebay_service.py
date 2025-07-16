import requests
import base64
import json
import tempfile
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import config

class EbayService:
    """Service for eBay API integration - listing creation and management"""
    
    def __init__(self):
        self.app_id = config.EBAY_APP_ID
        self.cert_id = config.EBAY_CERT_ID
        self.dev_id = config.EBAY_DEV_ID
        self.sandbox_auth_token = config.EBAY_SANDBOX_AUTH_TOKEN
        self.sandbox = config.EBAY_SANDBOX
        self.base_url = config.EBAY_BASE_URL
        self.oauth_url = config.EBAY_OAUTH_URL
        
        # Check if eBay is properly configured
        self.enabled = all([self.app_id, self.cert_id, self.dev_id, self.sandbox_auth_token])
        
        if not self.enabled:
            print("Warning: eBay service not properly configured - missing API credentials")
        else:
            print(f"eBay service initialized - Sandbox: {self.sandbox}")
    
    def get_application_token(self) -> Optional[str]:
        """Get application access token for eBay API"""
        
        if not self.enabled:
            return None
            
        try:
            # Create basic auth header
            credentials = f"{self.app_id}:{self.cert_id}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Basic {encoded_credentials}'
            }
            
            data = {
                'grant_type': 'client_credentials',
                'scope': 'https://api.ebay.com/oauth/api_scope'
            }
            
            response = requests.post(self.oauth_url, headers=headers, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data.get('access_token')
            else:
                print(f"Failed to get eBay application token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error getting eBay application token: {str(e)}")
            return None
    
    async def upload_image_to_eps(self, image_data: str, filename: str = "item_image.jpg") -> Optional[str]:
        """Upload image to eBay Picture Service (EPS)"""
        
        if not self.enabled:
            return None
            
        try:
            # Convert base64 to file
            image_bytes = base64.b64decode(image_data)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_file.write(image_bytes)
                temp_path = temp_file.name
            
            # Prepare XML payload for EPS
            xml_payload = f"""<?xml version="1.0" encoding="utf-8"?>
            <UploadSiteHostedPicturesRequest xmlns="urn:ebay:apis:eBLBaseComponents">
                <RequesterCredentials>
                    <eBayAuthToken>{self.sandbox_auth_token}</eBayAuthToken>
                </RequesterCredentials>
                <ExtensionInDays>30</ExtensionInDays>
                <PictureName>{filename}</PictureName>
            </UploadSiteHostedPicturesRequest>"""
            
            # Prepare multipart form data
            files = {
                'XML Payload': (None, xml_payload, 'text/xml'),
                'image': (filename, open(temp_path, 'rb'), 'image/jpeg')
            }
            
            # eBay Trading API endpoint for picture upload
            upload_url = f"{self.base_url}/ws/api.dll"
            
            headers = {
                'X-EBAY-API-COMPATIBILITY-LEVEL': '967',
                'X-EBAY-API-CALL-NAME': 'UploadSiteHostedPictures',
                'X-EBAY-API-SITEID': '0'  # US site
            }
            
            response = requests.post(upload_url, files=files, headers=headers)
            
            # Clean up temp file
            os.unlink(temp_path)
            
            if response.status_code == 200:
                # Parse XML response to get picture URL
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                
                # Find the picture URL in the response
                for elem in root.iter():
                    if 'FullURL' in elem.tag:
                        picture_url = elem.text
                        print(f"Successfully uploaded image to eBay EPS: {picture_url}")
                        return picture_url
                
                print("Image uploaded but could not find picture URL in response")
                return None
            else:
                print(f"Failed to upload image to eBay EPS: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error uploading image to eBay EPS: {str(e)}")
            return None
    
    async def create_inventory_item(self, item_data: Dict[str, Any]) -> Optional[str]:
        """Create inventory item using eBay Inventory API"""
        
        if not self.enabled:
            return None
            
        try:
            # Get application token
            access_token = self.get_application_token()
            if not access_token:
                return None
            
            # Generate SKU
            sku = f"SmartScape_{item_data.get('id', 'unknown')}_{int(datetime.now().timestamp())}"
            
            # Upload image first
            image_url = None
            if item_data.get('frame_data'):
                image_url = await self.upload_image_to_eps(
                    item_data['frame_data'], 
                    f"{item_data.get('name', 'item').replace(' ', '_')}.jpg"
                )
            
            # Prepare inventory item payload
            inventory_payload = {
                "availability": {
                    "shipToLocationAvailability": {
                        "quantity": 1
                    }
                },
                "condition": self._map_condition(item_data.get('condition', 'good')),
                "product": {
                    "title": item_data.get('name', 'Item'),
                    "description": item_data.get('description', f"A {item_data.get('name', 'item')} in {item_data.get('condition', 'good')} condition"),
                    "aspects": {
                        "Brand": ["Unbranded"],
                        "Type": [item_data.get('category', 'Other')]
                    }
                }
            }
            
            # Add image if uploaded successfully
            if image_url:
                inventory_payload["product"]["imageUrls"] = [image_url]
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Create inventory item
            inventory_url = f"{self.base_url}/sell/inventory/v1/inventory_item/{sku}"
            response = requests.put(inventory_url, headers=headers, json=inventory_payload)
            
            if response.status_code in [200, 201, 204]:
                print(f"Successfully created eBay inventory item: {sku}")
                return sku
            else:
                print(f"Failed to create eBay inventory item: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error creating eBay inventory item: {str(e)}")
            return None
    
    async def create_offer(self, sku: str, item_data: Dict[str, Any]) -> Optional[str]:
        """Create offer for inventory item"""
        
        if not self.enabled:
            return None
            
        try:
            # Get application token
            access_token = self.get_application_token()
            if not access_token:
                return None
            
            # Generate offer ID
            offer_id = f"OFFER_{sku}_{int(datetime.now().timestamp())}"
            
            # Prepare offer payload
            offer_payload = {
                "sku": sku,
                "marketplaceId": "EBAY_US",
                "format": "FIXED_PRICE",
                "availableQuantity": 1,
                "categoryId": self._get_ebay_category_id(item_data.get('category', 'Other')),
                "listingDescription": item_data.get('description', f"A {item_data.get('name', 'item')} in {item_data.get('condition', 'good')} condition"),
                "listingPolicies": {
                    "fulfillmentPolicyId": "6055773000",  # Default fulfillment policy
                    "paymentPolicyId": "6055774000",      # Default payment policy
                    "returnPolicyId": "6055775000"        # Default return policy
                },
                "pricingSummary": {
                    "price": {
                        "value": str(item_data.get('estimated_price', 50.0)),
                        "currency": "USD"
                    }
                },
                "quantityLimitPerBuyer": 1,
                "tax": {
                    "applyTax": False
                }
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Create offer
            offer_url = f"{self.base_url}/sell/inventory/v1/offer"
            response = requests.post(offer_url, headers=headers, json=offer_payload)
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                offer_id = response_data.get('offerId')
                print(f"Successfully created eBay offer: {offer_id}")
                return offer_id
            else:
                print(f"Failed to create eBay offer: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error creating eBay offer: {str(e)}")
            return None
    
    async def publish_offer(self, offer_id: str) -> bool:
        """Publish offer to eBay marketplace"""
        
        if not self.enabled:
            return False
            
        try:
            # Get application token
            access_token = self.get_application_token()
            if not access_token:
                return False
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Publish offer
            publish_url = f"{self.base_url}/sell/inventory/v1/offer/{offer_id}/publish"
            response = requests.post(publish_url, headers=headers)
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                listing_id = response_data.get('listingId')
                print(f"Successfully published eBay listing: {listing_id}")
                return True
            else:
                print(f"Failed to publish eBay offer: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error publishing eBay offer: {str(e)}")
            return False
    
    async def create_listing(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete eBay listing creation workflow"""
        
        if not self.enabled:
            return {
                "success": False,
                "error": "eBay service not properly configured"
            }
        
        try:
            # Step 1: Create inventory item
            sku = await self.create_inventory_item(item_data)
            if not sku:
                return {
                    "success": False,
                    "error": "Failed to create inventory item"
                }
            
            # Step 2: Create offer
            offer_id = await self.create_offer(sku, item_data)
            if not offer_id:
                return {
                    "success": False,
                    "error": "Failed to create offer"
                }
            
            # Step 3: Publish offer
            published = await self.publish_offer(offer_id)
            if not published:
                return {
                    "success": False,
                    "error": "Failed to publish listing"
                }
            
            return {
                "success": True,
                "sku": sku,
                "offer_id": offer_id,
                "marketplace": "eBay",
                "sandbox": self.sandbox,
                "message": f"Successfully listed '{item_data.get('name', 'item')}' on eBay!"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating eBay listing: {str(e)}"
            }
    
    def _map_condition(self, condition: str) -> str:
        """Map internal condition to eBay condition"""
        condition_map = {
            'excellent': 'NEW',
            'good': 'USED_EXCELLENT',
            'fair': 'USED_GOOD',
            'poor': 'USED_ACCEPTABLE'
        }
        return condition_map.get(condition.lower(), 'USED_GOOD')
    
    def _get_ebay_category_id(self, category: str) -> str:
        """Get eBay category ID for item category"""
        # Simplified category mapping - in production, use eBay's GetCategories API
        category_map = {
            'furniture': '3197',      # Home & Garden > Furniture
            'electronics': '293',     # Consumer Electronics
            'appliances': '20710',    # Home & Garden > Major Appliances
            'decor': '20518',         # Home & Garden > Home Décor
            'sports': '888',          # Sporting Goods
            'books': '267',           # Books
            'clothing': '11450'       # Clothing, Shoes & Accessories
        }
        return category_map.get(category.lower(), '99')  # Everything Else
    
    async def get_listing_status(self, offer_id: str) -> Dict[str, Any]:
        """Get status of eBay listing"""
        
        if not self.enabled:
            return {"error": "eBay service not configured"}
            
        try:
            access_token = self.get_application_token()
            if not access_token:
                return {"error": "Could not get access token"}
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            }
            
            # Get offer details
            offer_url = f"{self.base_url}/sell/inventory/v1/offer/{offer_id}"
            response = requests.get(offer_url, headers=headers)
            
            if response.status_code == 200:
                offer_data = response.json()
                return {
                    "success": True,
                    "status": offer_data.get('status', 'unknown'),
                    "listing_id": offer_data.get('listingId'),
                    "price": offer_data.get('pricingSummary', {}).get('price', {}),
                    "quantity": offer_data.get('availableQuantity', 0)
                }
            else:
                return {"error": f"Failed to get listing status: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Error getting listing status: {str(e)}"}
