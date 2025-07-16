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
import base64
import tempfile

class UseThisAutomation:
    def __init__(self):
        self.driver = None
        self.session_file = "usethis_session.json"
        self.cookies_file = "usethis_cookies.pkl"
        self.base_url = "https://use-this.netlify.app"
        
    def setup_driver(self):
        """Setup Chrome driver with stealth options"""
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--headless")  # Run in headless mode for server
        
        # Use regular Chrome driver instead of undetected chrome
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            print(f"Failed to setup Chrome driver: {e}")
            # Fallback to basic setup
            self.driver = webdriver.Chrome(options=options)

    def login_to_usethis(self, email: str, password: str = None):
        """Login to UseThis platform"""
        if not self.driver:
            self.setup_driver()
            
        try:
            # Try to load existing session
            if self.load_session():
                print("Loaded existing UseThis session")
                return True
                
            # Navigate to UseThis platform
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Look for login/signup buttons
            try:
                # Try to find login button
                login_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Login') or contains(text(), 'Sign In')]"))
                )
                login_button.click()
                time.sleep(2)
                
                # Enter email
                email_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='email' or @placeholder*='email']"))
                )
                email_field.send_keys(email)
                
                # If password field exists, enter password
                if password:
                    try:
                        password_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
                        password_field.send_keys(password)
                    except:
                        pass
                
                # Submit form
                submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit' or contains(text(), 'Login') or contains(text(), 'Sign In')]")
                submit_button.click()
                
                # Wait for login to complete
                time.sleep(5)
                
                # Save session
                self.save_session()
                print("Successfully logged into UseThis")
                return True
                
            except Exception as e:
                print(f"Login flow not found, continuing without login: {str(e)}")
                # Platform might not require login for posting
                return True
                
        except Exception as e:
            print(f"UseThis login failed: {str(e)}")
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
            print(f"Failed to save UseThis session: {str(e)}")
    
    def load_session(self):
        """Load existing session"""
        try:
            if not os.path.exists(self.cookies_file):
                return False
                
            # Load cookies
            self.driver.get(self.base_url)
            time.sleep(2)
            
            with open(self.cookies_file, 'rb') as f:
                cookies = pickle.load(f)
                
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except:
                    pass
                
            # Refresh to apply cookies
            self.driver.refresh()
            time.sleep(3)
            
            return True
                
        except Exception as e:
            print(f"Failed to load UseThis session: {str(e)}")
            
        return False
    
    def post_to_usethis(self, listing_data: Dict):
        """Post item to UseThis rental marketplace"""
        try:
            if not self.driver:
                self.setup_driver()
                
            # Navigate to UseThis platform
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Look for "List Item" or "Add Item" button
            try:
                list_item_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'List') or contains(text(), 'Add') or contains(text(), 'Post') or contains(text(), 'Rent')]"))
                )
                list_item_button.click()
                time.sleep(3)
            except:
                print("Could not find add item button, trying to post directly")
            
            # Fill item title - "WHAT ARE YOU SHARING?"
            try:
                title_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'WHAT ARE YOU SHARING') or @name='title' or @id='title']"))
                )
                title_field.clear()
                title_field.send_keys(listing_data['title'])
                print(f"Filled title: {listing_data['title']}")
            except:
                print("Could not find title field")
            
            # Select category
            try:
                category_dropdown = self.driver.find_element(By.XPATH, "//select[contains(@name, 'category') or contains(@id, 'category')] | //div[contains(text(), 'SELECT CATEGORY')]")
                if category_dropdown.tag_name == 'select':
                    category_dropdown.click()
                    # Try to select appropriate category
                    category_options = self.driver.find_elements(By.XPATH, "//select[contains(@name, 'category')]/option")
                    for option in category_options:
                        if any(cat in option.text.lower() for cat in [listing_data.get('category', '').lower(), 'furniture', 'electronics', 'other']):
                            option.click()
                            break
                else:
                    category_dropdown.click()
                    time.sleep(1)
                    # Look for category options
                    category_option = self.driver.find_element(By.XPATH, f"//div[contains(text(), '{listing_data.get('category', 'Other')}')]")
                    category_option.click()
                print(f"Selected category: {listing_data.get('category', 'Other')}")
            except:
                print("Could not find category field")
            
            # Fill description - "DESCRIBE YOUR ITEM IN DETAIL..."
            try:
                description_field = self.driver.find_element(By.XPATH, "//textarea[contains(@placeholder, 'DESCRIBE YOUR ITEM') or @name='description' or @id='description']")
                description_field.clear()
                description_field.send_keys(listing_data['description'])
                print(f"Filled description: {listing_data['description'][:50]}...")
            except:
                print("Could not find description field")
            
            # Fill location - "WHERE IS THIS ITEM?"
            try:
                location_field = self.driver.find_element(By.XPATH, "//input[contains(@placeholder, 'WHERE IS THIS ITEM') or @name='location' or @id='location']")
                location_field.clear()
                location_field.send_keys("Campus Area")
                print("Filled location: Campus Area")
            except:
                print("Could not find location field")
            
            # Fill price per day
            try:
                price_field = self.driver.find_element(By.XPATH, "//input[@type='number' or contains(@placeholder, 'PRICE PER DAY') or @name='price' or @id='price']")
                price_field.clear()
                # Convert sale price to rental price (roughly 1/30th for daily rental)
                rental_price = max(1, round(listing_data['price'] / 30, 2))
                price_field.send_keys(str(rental_price))
                print(f"Filled price: ${rental_price}/day")
            except:
                print("Could not find price field")
            
            # Set availability dates
            try:
                # Available from (today)
                from_date_field = self.driver.find_element(By.XPATH, "//input[@type='date' or contains(@placeholder, 'mm/dd/yyyy')]")
                from datetime import datetime, timedelta
                today = datetime.now().strftime('%m/%d/%Y')
                from_date_field.send_keys(today)
                
                # Available until (30 days from now)
                until_date_field = self.driver.find_elements(By.XPATH, "//input[@type='date' or contains(@placeholder, 'mm/dd/yyyy')]")[1]
                future_date = (datetime.now() + timedelta(days=30)).strftime('%m/%d/%Y')
                until_date_field.send_keys(future_date)
                print(f"Set availability: {today} to {future_date}")
            except:
                print("Could not find availability fields")
            
            # Upload photos if available
            if listing_data.get('image_data'):
                self.upload_photos(listing_data['image_data'])
            
            # Submit the listing - "CREATE LISTING"
            try:
                submit_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'CREATE LISTING') or contains(text(), 'CREATE') or @type='submit']"))
                )
                submit_button.click()
                
                # Wait for confirmation
                time.sleep(5)
                
                print(f"Successfully posted to UseThis: {listing_data['title']}")
                return True
                
            except Exception as e:
                print(f"Could not submit listing: {str(e)}")
                return False
            
        except Exception as e:
            print(f"Failed to post to UseThis: {str(e)}")
            return False
    
    def upload_photos(self, image_data: str):
        """Upload photos from base64 data"""
        try:
            # Convert base64 to file
            image_bytes = base64.b64decode(image_data)
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_file.write(image_bytes)
                temp_path = temp_file.name
            
            # Find upload button/input
            try:
                upload_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
                upload_input.send_keys(temp_path)
                time.sleep(3)
            except:
                # Try alternative upload methods
                try:
                    upload_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Upload') or contains(text(), 'Photo')]")
                    upload_button.click()
                    time.sleep(1)
                    upload_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
                    upload_input.send_keys(temp_path)
                    time.sleep(3)
                except:
                    print("Could not find photo upload")
            
            # Clean up temp file
            os.unlink(temp_path)
            
        except Exception as e:
            print(f"Failed to upload photos to UseThis: {str(e)}")
    
    def get_posted_listings(self):
        """Get list of posted listings from UseThis"""
        try:
            if not self.driver:
                return []
                
            # Navigate to user's listings/profile
            self.driver.get(f"{self.base_url}/profile")
            time.sleep(3)
            
            # Extract listing information
            listings = []
            listing_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'listing') or contains(@class, 'item')]")
            
            for element in listing_elements:
                try:
                    title = element.find_element(By.XPATH, ".//h3 | .//h2 | .//h4").text
                    price = element.find_element(By.XPATH, ".//*[contains(text(), '$')]").text
                    
                    listings.append({
                        "title": title,
                        "price": price,
                        "status": "active"
                    })
                except:
                    continue
            
            return listings
            
        except Exception as e:
            print(f"Failed to get UseThis listings: {str(e)}")
            return []
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None
