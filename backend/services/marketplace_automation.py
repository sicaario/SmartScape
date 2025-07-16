import time
import json
import pickle
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc
from typing import Dict, List
import config

class MarketplaceAutomation:
    def __init__(self):
        self.driver = None
        self.session_file = "facebook_session.json"
        self.cookies_file = "facebook_cookies.pkl"
        
    def setup_driver(self):
        """Setup Chrome driver with stealth options"""
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Use undetected chrome to avoid detection
        self.driver = uc.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def login_to_facebook(self, email: str, password: str):
        """Login to Facebook and save session"""
        if not self.driver:
            self.setup_driver()
            
        try:
            # Try to load existing session
            if self.load_session():
                print("Loaded existing Facebook session")
                return True
                
            # Fresh login
            self.driver.get("https://www.facebook.com/login")
            time.sleep(3)
            
            # Enter credentials
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            password_field = self.driver.find_element(By.ID, "pass")
            
            email_field.send_keys(email)
            password_field.send_keys(password)
            
            # Click login
            login_button = self.driver.find_element(By.NAME, "login")
            login_button.click()
            
            # Wait for login to complete
            WebDriverWait(self.driver, 15).until(
                EC.url_contains("facebook.com")
            )
            
            # Save session
            self.save_session()
            print("Successfully logged into Facebook")
            return True
            
        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False
    
    def save_session(self):
        """Save cookies and session data"""
        try:
            # Save cookies
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(self.driver.get_cookies(), f)
                
            # Save session info
            session_data = {
                "current_url": self.driver.current_url,
                "user_agent": self.driver.execute_script("return navigator.userAgent;")
            }
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f)
                
        except Exception as e:
            print(f"Failed to save session: {str(e)}")
    
    def load_session(self):
        """Load existing session"""
        try:
            if not os.path.exists(self.cookies_file):
                return False
                
            # Load cookies
            self.driver.get("https://www.facebook.com")
            time.sleep(2)
            
            with open(self.cookies_file, 'rb') as f:
                cookies = pickle.load(f)
                
            for cookie in cookies:
                self.driver.add_cookie(cookie)
                
            # Refresh to apply cookies
            self.driver.refresh()
            time.sleep(3)
            
            # Check if still logged in
            if "login" not in self.driver.current_url.lower():
                return True
                
        except Exception as e:
            print(f"Failed to load session: {str(e)}")
            
        return False
    
    def post_to_marketplace(self, listing_data: Dict):
        """Post item to Facebook Marketplace"""
        try:
            if not self.driver:
                raise Exception("Driver not initialized")
                
            # Navigate to Marketplace
            self.driver.get("https://www.facebook.com/marketplace/create/item")
            time.sleep(5)
            
            # Upload photos
            if listing_data.get('image_data'):
                self.upload_photos(listing_data['image_data'])
            
            # Fill title
            title_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='What are you selling?']"))
            )
            title_field.send_keys(listing_data['title'])
            
            # Fill price
            price_field = self.driver.find_element(By.XPATH, "//input[@placeholder='Price']")
            price_field.send_keys(str(listing_data['price']))
            
            # Select category (simplified)
            category_button = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Category')]")
            category_button.click()
            time.sleep(2)
            
            # Fill description
            description_field = self.driver.find_element(By.XPATH, "//textarea[@placeholder='Describe your item']")
            description_field.send_keys(listing_data['description'])
            
            # Set location (use current location)
            time.sleep(2)
            
            # Publish listing
            publish_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Publish')]"))
            )
            publish_button.click()
            
            # Wait for confirmation
            time.sleep(5)
            
            print(f"Successfully posted: {listing_data['title']}")
            return True
            
        except Exception as e:
            print(f"Failed to post listing: {str(e)}")
            return False
    
    def upload_photos(self, image_data: str):
        """Upload photos from base64 data"""
        try:
            # Convert base64 to file
            import base64
            import tempfile
            
            image_bytes = base64.b64decode(image_data)
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_file.write(image_bytes)
                temp_path = temp_file.name
            
            # Find upload button
            upload_button = self.driver.find_element(By.XPATH, "//input[@type='file']")
            upload_button.send_keys(temp_path)
            
            # Wait for upload
            time.sleep(3)
            
            # Clean up temp file
            os.unlink(temp_path)
            
        except Exception as e:
            print(f"Failed to upload photos: {str(e)}")
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None
