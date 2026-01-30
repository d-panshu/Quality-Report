"""
Production Configuration File
Handles environment variables and production settings
"""
import os
from datetime import date

# ==================== GOOGLE SHEETS CONFIGURATION ====================
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1jGqY8HxhS63vjGnJeKbYUBpuW3iNI_nQzADmMfv_ioE")
SHEET_NAME = os.getenv("SHEET_NAME", "Daily Fruits & Vegetables Quality Photo Upload (Responses)")

# ==================== DIRECTORY CONFIGURATION ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.getenv("IMAGE_DIR", os.path.join(BASE_DIR, "data", "images"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.join(BASE_DIR, "output"))
ASSETS_DIR = os.getenv("ASSETS_DIR", os.path.join(BASE_DIR, "assets"))

# ==================== DATE CONFIGURATION ====================
# Use environment variable for date or default to today
DATE_OVERRIDE = os.getenv("REPORT_DATE", None)
if DATE_OVERRIDE:
    TODAY_STR = DATE_OVERRIDE
else:
    TODAY_STR = date.today().strftime("%Y-%m-%d")

# ==================== IMAGE DIMENSIONS (in cm, converted to inches) ====================
# PDF dimensions from mockup
PRODUCT_IMAGE_WIDTH_CM = 5.77
PRODUCT_IMAGE_HEIGHT_CM = 7.7
OVERALL_IMAGE_WIDTH_CM = 9.44
OVERALL_IMAGE_HEIGHT_CM = 7.07

# Convert cm to inches (1 inch = 2.54 cm)
CM_TO_INCH = 1 / 2.54
PRODUCT_IMAGE_WIDTH = PRODUCT_IMAGE_WIDTH_CM * CM_TO_INCH
PRODUCT_IMAGE_HEIGHT = PRODUCT_IMAGE_HEIGHT_CM * CM_TO_INCH
OVERALL_IMAGE_WIDTH = OVERALL_IMAGE_WIDTH_CM * CM_TO_INCH
OVERALL_IMAGE_HEIGHT = OVERALL_IMAGE_HEIGHT_CM * CM_TO_INCH

# ==================== FILE VALIDATION ====================
# Valid image file extensions
VALID_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']

# Placeholder for missing images
PLACEHOLDER_IMAGE = os.path.join(ASSETS_DIR, "not_uploaded.png")

# ==================== LOGGING CONFIGURATION ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = os.getenv("LOG_FILE", os.path.join(OUTPUT_DIR, "quality_report.log"))

# ==================== ERROR HANDLING ====================
# Continue processing even if individual images fail
CONTINUE_ON_ERROR = os.getenv("CONTINUE_ON_ERROR", "true").lower() == "true"

# Maximum retries for download failures
MAX_DOWNLOAD_RETRIES = int(os.getenv("MAX_DOWNLOAD_RETRIES", "3"))

# Timeout for API requests (seconds)
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

# ==================== PERFORMANCE ====================
# Enable/disable temp file cleanup
CLEANUP_TEMP_FILES = os.getenv("CLEANUP_TEMP_FILES", "true").lower() == "true"

# ==================== VALIDATION ====================
def validate_config():
    """Validate configuration and create necessary directories"""
    errors = []
    
    # Check required directories
    for dir_path in [IMAGE_DIR, OUTPUT_DIR, ASSETS_DIR]:
        os.makedirs(dir_path, exist_ok=True)
    
    # Check placeholder image exists
    if not os.path.exists(PLACEHOLDER_IMAGE):
        errors.append(f"Placeholder image not found: {PLACEHOLDER_IMAGE}")
    
    # Check credentials file exists
    if not os.path.exists(os.path.join(BASE_DIR, "credentials.json")):
        errors.append("credentials.json not found in project root")
    
    return errors

# Validate on import
config_errors = validate_config()
if config_errors:
    print("Configuration warnings:")
    for error in config_errors:
        print(f"  - {error}")