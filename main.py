"""
Production-Ready Daily Quality Report Generator
"""
import os
import re
import sys
import logging
from datetime import datetime
from drive_client import get_service, download_drive_file
from sheets_client import read_sheet
from config import (
    IMAGE_DIR, OUTPUT_DIR, TODAY_STR, PLACEHOLDER_IMAGE, 
    VALID_IMAGE_EXTENSIONS, CONTINUE_ON_ERROR, LOG_FILE, LOG_LEVEL
)
from pdf_generator import generate_daily_report_pdf
from PIL import Image

# ==================== LOGGING SETUP ====================
def setup_logging():
    """Configure logging for production"""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ==================== UTILITY FUNCTIONS ====================
def extract_file_id(url):
    """Extract Google Drive file ID from various URL formats"""
    if not url or not isinstance(url, str):
        return None

    patterns = [
        r"/d/([a-zA-Z0-9_-]+)",
        r"id=([a-zA-Z0-9_-]+)",
        r"/uc\?id=([a-zA-Z0-9_-]+)",
        r"open\?id=([a-zA-Z0-9_-]+)"
    ]

    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def normalize_date(val):
    """Convert date string to YYYY-MM-DD format"""
    try:
        return datetime.strptime(str(val).strip(), "%m/%d/%Y").strftime("%Y-%m-%d")
    except Exception as e:
        logger.warning(f"Failed to normalize date '{val}': {e}")
        return ""


def find_col(df, name):
    """Find column by name (case-insensitive)"""
    for c in df.columns:
        if c.strip().lower() == name.lower():
            return c
    return None


def extract_product_name(column_name):
    """Extract product name from column header"""
    return column_name.split("–")[0].strip()


def validate_image_file(file_path):
    """Validate that the downloaded file is a valid image"""
    if not os.path.exists(file_path):
        return False
    
    _, ext = os.path.splitext(file_path.lower())
    if ext not in VALID_IMAGE_EXTENSIONS:
        logger.warning(f"Invalid file extension: {ext} for {file_path}")
        return False
    
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception as e:
        logger.warning(f"Invalid image file {file_path}: {str(e)}")
        return False


# ==================== IMAGE DOWNLOAD FUNCTIONS ====================
def download_and_validate_image(drive, file_id, save_path, image_name):
    """
    Download and validate a single image
    Returns: (success: bool, path: str)
    """
    try:
        download_drive_file(drive, file_id, save_path)
        if validate_image_file(save_path):
            logger.info(f"✓ {image_name}: Downloaded and validated")
            return True, save_path
        else:
            if os.path.exists(save_path):
                os.remove(save_path)
            logger.warning(f"✗ {image_name}: Downloaded but failed validation")
            return False, PLACEHOLDER_IMAGE
    except Exception as e:
        logger.error(f"✗ {image_name}: Download error - {str(e)}")
        return False, PLACEHOLDER_IMAGE


def process_image_column(drive, first_row, col, save_path, image_name):
    """
    Process a single image column from the sheet
    Returns: path to image (valid image or placeholder)
    """
    cell = first_row[col]
    if hasattr(cell, "__iter__") and not isinstance(cell, str):
        cell = next((x for x in cell if x), "")

    link = str(cell).strip()
    if not link:
        logger.info(f"  {image_name}: No link provided")
        return PLACEHOLDER_IMAGE

    file_id = extract_file_id(link)
    if not file_id:
        logger.warning(f"  {image_name}: Could not extract file ID from link")
        return PLACEHOLDER_IMAGE

    success, path = download_and_validate_image(drive, file_id, save_path, image_name)
    return path


# ==================== MAIN PROCESSING ====================
def process_store_images(drive, first_row, store_name, store_dir, overall_columns, product_columns):
    """
    Process all images for a single store
    Returns: (overall_images, product_images)
    """
    # Download overall photos
    overall_images = []
    for idx, col in enumerate(overall_columns, 1):
        save_path = os.path.join(store_dir, f"Overall_{idx}.jpg")
        img_path = process_image_column(drive, first_row, col, save_path, f"Overall photo {idx}")
        overall_images.append(img_path)

    # Download product images
    product_images = []
    for col in product_columns:
        product = extract_product_name(col)
        save_path = os.path.join(store_dir, f"{product}.jpg")
        img_path = process_image_column(drive, first_row, col, save_path, product)
        product_images.append((product, img_path))

    # Sort product images alphabetically
    product_images = sorted(product_images, key=lambda x: x[0].lower())
    
    return overall_images, product_images


def main():
    """Main function to process all stores and generate PDF report"""
    try:
        logger.info("="*60)
        logger.info(f"Starting Daily Quality Report Generation for {TODAY_STR}")
        logger.info("="*60)
        
        # Create directories
        os.makedirs(IMAGE_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Get Google services
        logger.info("Authenticating with Google services...")
        drive, sheets = get_service()
        logger.info("Authentication successful")

        # Read sheet data
        logger.info("Reading sheet data...")
        df = read_sheet(sheets)
        logger.info(f"Found {len(df)} total rows in sheet")

        # Find metadata columns
        date_col = find_col(df, "Date")
        store_col = find_col(df, "Store Name")
        email_col = find_col(df, "Email Address")
        name_col = find_col(df, "Name")
        phone_col = find_col(df, "Phone Number")

        if not all([date_col, store_col, name_col, phone_col]):
            logger.error("Missing required columns in sheet")
            return

        # Filter for today's submissions
        df["__date"] = df[date_col].apply(normalize_date)
        df_today = df[df["__date"] == TODAY_STR]

        if df_today.empty:
            logger.warning(f"No submissions found for {TODAY_STR}")
            return

        logger.info(f"Found {len(df_today)} submissions for {TODAY_STR}")

        # Find overall photo columns
        overall_columns = sorted(
            [c for c in df.columns if "overall" in c.lower() and "photo" in c.lower()],
            key=lambda x: x.lower()
        )
        logger.info(f"Found {len(overall_columns)} overall photo columns")

        # Find product columns (exclude overall photos)
        product_columns = [
            c for c in df.columns 
            if "take a clear photo" in c.lower() 
            and c not in overall_columns
        ]
        logger.info(f"Found {len(product_columns)} product columns")
        for col in product_columns:
            logger.debug(f"  - {extract_product_name(col)}")

        # Process each store
        all_stores_data = []
        stores = df_today[store_col].unique()
        
        for store_idx, store in enumerate(stores, 1):
            store = str(store).strip()
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing store {store_idx}/{len(stores)}: {store}")
            logger.info(f"{'='*60}")
            
            store_dir = os.path.join(IMAGE_DIR, store.replace(" ", "_"))
            os.makedirs(store_dir, exist_ok=True)

            # Get first row for this store
            store_df = df_today[df_today[store_col] == store]
            first_row = store_df.iloc[0]
            
            # Extract metadata
            meta = {
                "store_name": store,
                "email": str(first_row[email_col]) if email_col else "",
                "name": str(first_row[name_col]) if name_col else "",
                "phone": str(first_row[phone_col]) if phone_col else "",
                "date": TODAY_STR
            }

            # Process images
            try:
                overall_images, product_images = process_store_images(
                    drive, first_row, store, store_dir, overall_columns, product_columns
                )

                all_stores_data.append({
                    "meta": meta,
                    "overall_images": overall_images,
                    "product_images": product_images
                })
                
                logger.info(f"✓ Store '{store}' processed successfully")
                
            except Exception as e:
                logger.error(f"✗ Error processing store '{store}': {str(e)}")
                if not CONTINUE_ON_ERROR:
                    raise

        # Generate PDF
        if all_stores_data:
            logger.info(f"\n{'='*60}")
            logger.info("Generating PDF report...")
            pdf_path = generate_daily_report_pdf(all_stores_data, TODAY_STR)
            logger.info(f"✓ PDF Report Generated: {pdf_path}")
            logger.info(f"Total stores processed: {len(all_stores_data)}")
            logger.info(f"{'='*60}")
            return pdf_path
        else:
            logger.warning("No data to generate PDF")
            return None

    except Exception as e:
        logger.error(f"Fatal error in main process: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        result = main()
        if result:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        logger.error(f"Application failed: {str(e)}")
        sys.exit(1)