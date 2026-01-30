import os
from datetime import date

# Google Sheet details
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1jGqY8HxhS63vjGnJeKbYUBpuW3iNI_nQzADmMfv_ioE")
SHEET_NAME = os.getenv("SHEET_NAME", "Daily Fruits & Vegetables Quality Photo Upload (Responses)")

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # project folder
IMAGE_DIR = os.getenv("IMAGE_DIR", os.path.join(BASE_DIR, "data", "images"))  
OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.join(BASE_DIR, "output")) 
ASSETS_DIR = os.getenv("ASSETS_DIR", os.path.join(BASE_DIR, "assets"))  

# Report date
DATE_OVERRIDE = os.getenv("REPORT_DATE", None) 
if DATE_OVERRIDE:
    TODAY_STR = DATE_OVERRIDE  
else:
    TODAY_STR = date.today().strftime("%Y-%m-%d") 

# Image size in cm
PRODUCT_IMAGE_WIDTH_CM = 5.77
PRODUCT_IMAGE_HEIGHT_CM = 7.7
OVERALL_IMAGE_WIDTH_CM = 9.44
OVERALL_IMAGE_HEIGHT_CM = 7.07

# cm to inch
CM_TO_INCH = 1 / 2.54
PRODUCT_IMAGE_WIDTH = PRODUCT_IMAGE_WIDTH_CM * CM_TO_INCH
PRODUCT_IMAGE_HEIGHT = PRODUCT_IMAGE_HEIGHT_CM * CM_TO_INCH
OVERALL_IMAGE_WIDTH = OVERALL_IMAGE_WIDTH_CM * CM_TO_INCH
OVERALL_IMAGE_HEIGHT = OVERALL_IMAGE_HEIGHT_CM * CM_TO_INCH

# Image formats
VALID_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']

# Default image
PLACEHOLDER_IMAGE = os.path.join(ASSETS_DIR, "not_uploaded.png")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  
LOG_FILE = os.getenv("LOG_FILE", os.path.join(OUTPUT_DIR, "quality_report.log")) 

# Error handling
CONTINUE_ON_ERROR = os.getenv("CONTINUE_ON_ERROR", "true").lower() == "true" 
MAX_DOWNLOAD_RETRIES = int(os.getenv("MAX_DOWNLOAD_RETRIES", "3")) 
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30")) 

# Cleanup
CLEANUP_TEMP_FILES = os.getenv("CLEANUP_TEMP_FILES", "true").lower() == "true"  

# Check setup
def validate_config():
    """Check folders and files"""
    errors = []
    
    for dir_path in [IMAGE_DIR, OUTPUT_DIR, ASSETS_DIR]:
        os.makedirs(dir_path, exist_ok=True)
    
    if not os.path.exists(PLACEHOLDER_IMAGE):
        errors.append(f"Placeholder image not found: {PLACEHOLDER_IMAGE}")
    
    if not os.path.exists(os.path.join(BASE_DIR, "credentials.json")):
        errors.append("credentials.json not found")
    
    return errors

config_errors = validate_config()
if config_errors:
    print("Configuration warnings:")
    for error in config_errors:
        print(f"  - {error}")
