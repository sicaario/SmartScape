from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.id import ID
import config
import base64
import tempfile
import os
from typing import Dict, List
from datetime import datetime

class AppwriteService:
    def __init__(self):
        self.client = Client()
        self.client.set_endpoint(config.APPWRITE_ENDPOINT)
        self.client.set_project(config.APPWRITE_PROJECT_ID)
        self.client.set_key(config.APPWRITE_API_KEY)
        
        self.databases = Databases(self.client)
        self.storage = Storage(self.client)
        
        self.database_id = config.APPWRITE_DATABASE_ID
        self.saved_items_collection_id = "68604d09001d229173f2"  # Actual collection ID from Appwrite
        self.sell_items_collection_id = "sell_items"  # Sell mode extracted items
        self.bucket_id = "6860506f002eb0873e7c"  # User's storage bucket ID
    
    async def upload_image(self, image_data: str, user_id: str, image_type: str, original_filename: str = None) -> str:
        """Upload base64 image to Appwrite storage and save metadata to database"""
        
        try:
            # Convert base64 to file
            image_bytes = base64.b64decode(image_data)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_file.write(image_bytes)
                temp_path = temp_file.name
            
            # Generate unique file ID
            file_id = ID.unique()
            
            # Upload to Appwrite storage
            file_result = self.storage.create_file(
                bucket_id=self.bucket_id,
                file_id=file_id,
                file=open(temp_path, 'rb')
            )
            
            # Clean up temp file
            os.unlink(temp_path)
            
            # Get file URL
            image_url = f"{config.APPWRITE_ENDPOINT}/storage/buckets/{self.bucket_id}/files/{file_id}/view?project={config.APPWRITE_PROJECT_ID}"
            
            # Save metadata to database
            image_doc = self.databases.create_document(
                database_id=self.database_id,
                collection_id=self.saved_items_collection_id,
                document_id=ID.unique(),
                data={
                    "image_id": file_id,
                    "user_id": user_id,
                    "image_url": image_url,
                    "image_type": image_type,
                    "original_filename": original_filename or "unknown.jpg",
                    "created_at": datetime.now().isoformat()
                }
            )
            
            return image_url
            
        except Exception as e:
            print(f"Error uploading image to Appwrite: {str(e)}")
            raise Exception(f"Failed to upload image: {str(e)}")
    
    async def upload_image_to_storage_only(self, image_data: str, filename: str = None) -> str:
        """Upload base64 image to Appwrite storage only (no database)"""
        
        try:
            # Convert base64 to file
            image_bytes = base64.b64decode(image_data)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_file.write(image_bytes)
                temp_path = temp_file.name
            
            # Generate unique file ID
            file_id = ID.unique()
            
            # Upload to Appwrite storage
            file_result = self.storage.create_file(
                bucket_id=self.bucket_id,
                file_id=file_id,
                file=open(temp_path, 'rb')
            )
            
            # Clean up temp file
            os.unlink(temp_path)
            
            # Get file URL
            image_url = f"{config.APPWRITE_ENDPOINT}/storage/buckets/{self.bucket_id}/files/{file_id}/view?project={config.APPWRITE_PROJECT_ID}"
            
            print(f"Uploaded image to Appwrite storage: {image_url}")
            return image_url
            
        except Exception as e:
            print(f"Error uploading image to Appwrite storage: {str(e)}")
            raise Exception(f"Failed to upload image: {str(e)}")
    
    async def save_extracted_item(self, item: Dict, user_id: str, image_url: str) -> str:
        """Save extracted item to Appwrite database (sell mode)"""
        
        try:
            item_doc = self.databases.create_document(
                database_id=self.database_id,
                collection_id=self.sell_items_collection_id,  # Use separate collection for sell mode
                document_id=ID.unique(),
                data={
                    "item_id": item.get("id", ID.unique()),
                    "user_id": user_id,
                    "name": item["name"],
                    "category": item["category"],
                    "price": float(item["estimated_price"]),
                    "image_url": image_url,
                    "status": "draft",
                    "created_at": datetime.now().isoformat()
                }
            )
            
            return item_doc["$id"]
            
        except Exception as e:
            print(f"Error saving item to Appwrite: {str(e)}")
            raise Exception(f"Failed to save item: {str(e)}")
    
    async def get_user_items(self, user_id: str) -> List[Dict]:
        """Get all sell mode items for a user"""
        
        try:
            result = self.databases.list_documents(
                database_id=self.database_id,
                collection_id=self.sell_items_collection_id,  # Use separate collection for sell mode
                queries=[f'equal("user_id", "{user_id}")']
            )
            
            return result["documents"]
            
        except Exception as e:
            print(f"Error getting user items: {str(e)}")
            return []
    
    async def update_item_status(self, item_id: str, status: str) -> bool:
        """Update sell mode item status (draft/listed/sold)"""
        
        try:
            self.databases.update_document(
                database_id=self.database_id,
                collection_id=self.sell_items_collection_id,  # Use separate collection for sell mode
                document_id=item_id,
                data={"status": status}
            )
            
            return True
            
        except Exception as e:
            print(f"Error updating item status: {str(e)}")
            return False
    
    async def save_buy_recommendation(self, user_id: str, product_data: Dict) -> str:
        """Save a product recommendation from buy mode to SmartScape collection"""
        
        try:
            # Truncate description to fit Appwrite schema (150 char limit)
            description = product_data.get("description", "")
            if len(description) > 150:
                description = description[:147] + "..."
            
            saved_item = self.databases.create_document(
                database_id=self.database_id,
                collection_id=self.saved_items_collection_id,  # SmartScape collection for buy mode only
                document_id=ID.unique(),
                data={
                    "user_id": user_id,
                    "title": product_data.get("title", ""),
                    "description": description,
                    "url": product_data.get("url", ""),
                    "price": product_data.get("price", 0.0),
                    "category": product_data.get("category", ""),
                    "store": product_data.get("store", ""),
                    "source": product_data.get("source", "buy_mode"),
                    "suggestion_item": product_data.get("suggestion_item", ""),
                    "priority": product_data.get("priority", "medium"),
                    "status": "saved",
                    "saved_at": datetime.now().isoformat()
                }
            )
            
            return saved_item["$id"]
            
        except Exception as e:
            print(f"Error saving recommendation: {str(e)}")
            raise Exception(f"Failed to save recommendation: {str(e)}")
    
    async def get_saved_recommendations(self, user_id: str) -> List[Dict]:
        """Get all saved buy mode recommendations for a user from SmartScape collection"""
        
        try:
            from appwrite.query import Query
            
            result = self.databases.list_documents(
                database_id=self.database_id,
                collection_id=self.saved_items_collection_id,  # SmartScape collection for buy mode only
                queries=[Query.equal("user_id", user_id)]
            )
            
            return result["documents"]
            
        except Exception as e:
            print(f"Error getting saved recommendations: {str(e)}")
            return []
