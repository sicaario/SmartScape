import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables once at module import
def load_env():
    """Load environment variables from .env file"""
    # Try different possible locations for .env file
    possible_paths = [
        Path(__file__).parent / '.env',  # Same directory as config.py
        Path(__file__).parent.parent / '.env',  # Parent directory
        Path.cwd() / '.env',  # Current working directory
    ]
    
    for env_path in possible_paths:
        if env_path.exists():
            load_dotenv(env_path)
            print(f"Loaded .env from: {env_path}")
            break
    else:
        print("Warning: No .env file found in any of the expected locations:")
        for path in possible_paths:
            print(f"  - {path}")

# Load environment variables when this module is imported
load_env()

# Environment variables
NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Validation
if not NEBIUS_API_KEY:
    raise ValueError("NEBIUS_API_KEY environment variable is required")

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY environment variable is required")

print(f"Config loaded - NEBIUS_API_KEY: {'✓' if NEBIUS_API_KEY else '✗'}")
print(f"Config loaded - TAVILY_API_KEY: {'✓' if TAVILY_API_KEY else '✗'}")

# Appwrite configuration
APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT", "https://cloud.appwrite.io/v1")
APPWRITE_PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID", "685fdd8d0002f0bfc30e")
APPWRITE_API_KEY = os.getenv("APPWRITE_API_KEY")
APPWRITE_DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID", "68604cf100315501c071")

# Validation
if not APPWRITE_PROJECT_ID:
    print("Warning: APPWRITE_PROJECT_ID not set")
if not APPWRITE_API_KEY:
    print("Warning: APPWRITE_API_KEY not set")

print(f"Config loaded - APPWRITE_PROJECT_ID: {'✓' if APPWRITE_PROJECT_ID else '✗'}")
print(f"Config loaded - APPWRITE_API_KEY: {'✓' if APPWRITE_API_KEY else '✗'}")

# Mem0 configuration
MEM0_API_KEY = os.getenv("MEM0_API_KEY")

# Validation
if not MEM0_API_KEY:
    print("Warning: MEM0_API_KEY not set - personalization features will be disabled")

print(f"Config loaded - MEM0_API_KEY: {'✓' if MEM0_API_KEY else '✗'}")

# eBay configuration
EBAY_APP_ID = os.getenv("EBAY_APP_ID")  # Client ID
EBAY_CERT_ID = os.getenv("EBAY_CERT_ID")  # Client Secret
EBAY_DEV_ID = os.getenv("EBAY_DEV_ID")  # Developer ID
EBAY_SANDBOX_AUTH_TOKEN = os.getenv("EBAY_SANDBOX_AUTH_TOKEN")  # Sandbox auth token
EBAY_SANDBOX = os.getenv("EBAY_SANDBOX", "true").lower() == "true"

# eBay API endpoints
EBAY_BASE_URL = "https://api.sandbox.ebay.com" if EBAY_SANDBOX else "https://api.ebay.com"
EBAY_OAUTH_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token" if EBAY_SANDBOX else "https://api.ebay.com/identity/v1/oauth2/token"

# Validation
if not EBAY_APP_ID:
    print("Warning: EBAY_APP_ID not set - eBay features will be disabled")
if not EBAY_CERT_ID:
    print("Warning: EBAY_CERT_ID not set - eBay features will be disabled")
if not EBAY_DEV_ID:
    print("Warning: EBAY_DEV_ID not set - eBay features will be disabled")
if not EBAY_SANDBOX_AUTH_TOKEN:
    print("Warning: EBAY_SANDBOX_AUTH_TOKEN not set - eBay features will be disabled")

print(f"Config loaded - EBAY_APP_ID: {'✓' if EBAY_APP_ID else '✗'}")
print(f"Config loaded - EBAY_CERT_ID: {'✓' if EBAY_CERT_ID else '✗'}")
print(f"Config loaded - EBAY_DEV_ID: {'✓' if EBAY_DEV_ID else '✗'}")
print(f"Config loaded - EBAY_SANDBOX_AUTH_TOKEN: {'✓' if EBAY_SANDBOX_AUTH_TOKEN else '✗'}")
print(f"eBay Sandbox Mode: {'✓' if EBAY_SANDBOX else '✗'}")