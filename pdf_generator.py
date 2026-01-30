import os
import cv2
import numpy as np
from reportlab.platypus import (
    SimpleDocTemplate, Image, Paragraph, Spacer, Table, PageBreak, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from PIL import Image as PILImage
from config import (
    PRODUCT_IMAGE_WIDTH, PRODUCT_IMAGE_HEIGHT,
    OVERALL_IMAGE_WIDTH, OVERALL_IMAGE_HEIGHT,
    OUTPUT_DIR, PLACEHOLDER_IMAGE
)


def overlay_text_on_image(image_path, text, output_path):
    """
    Overlay subtle text on image using OpenCV
    Creates a very subtle semi-transparent bar at the bottom with small centered text
    Returns the path to the modified image
    """
    try:
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            return image_path
        
        h, w = img.shape[:2]
        
        # Create very subtle overlay bar at the bottom (12% of height - reduced from 20%)
        overlay = img.copy()
        bar_height = int(h * 0.12)  # Smaller bar for subtle appearance
        
        # Draw black rectangle for text background
        cv2.rectangle(overlay, (0, h - bar_height), (w, h), (0, 0, 0), -1)
        
        # Blend overlay with original image (35% opacity - much more subtle)
        alpha = 0.35  # Reduced from 0.70 for subtle effect
        img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
        
        # Configure text properties - smaller and lighter
        font = cv2.FONT_HERSHEY_SIMPLEX  # Cleaner, simpler font
        
        # Smaller font scaling
        font_scale = min(w, h) / 500  # Reduced from 350 for smaller text
        font_thickness = max(1, int(font_scale * 2))  # Thinner text
        
        # Get text size for centering
        (text_width, text_height), baseline = cv2.getTextSize(
            text, font, font_scale, font_thickness
        )
        
        # Center text horizontally and vertically in the bar
        text_x = (w - text_width) // 2
        text_y = h - (bar_height // 2) + (text_height // 2)
        
        # Draw text in white (no shadow for more subtle appearance)
        cv2.putText(img, text, (text_x, text_y), font, font_scale, 
                   (255, 255, 255), font_thickness, cv2.LINE_AA)
        
        # Save modified image
        cv2.imwrite(output_path, img)
        return output_path
        
    except Exception as e:
        print(f"Error overlaying text on {image_path}: {str(e)}")
        return image_path


def create_image_with_overlay(img_path, product_name, temp_dir):
    """
    Create a temporary image with product name overlaid using OpenCV
    Returns path to the temporary image
    """
    if not os.path.exists(img_path) or img_path == PLACEHOLDER_IMAGE:
        return img_path
    
    # Create temp directory if it doesn't exist
    os.makedirs(temp_dir, exist_ok=True)
    
    # Generate UNIQUE temp file path using full original path
    # This prevents different stores from overwriting each other's images
    # e.g., data/images/Store1/Onion.jpg -> temp_overlays/Store1_Onion_overlay.jpg
    #       data/images/Store2/Onion.jpg -> temp_overlays/Store2_Onion_overlay.jpg
    
    # Extract store directory name and filename
    parent_dir = os.path.basename(os.path.dirname(img_path))  # e.g., "Nirman_Nagar"
    filename = os.path.basename(img_path)  # e.g., "Onion.jpg"
    name, ext = os.path.splitext(filename)
    
    # Create unique temp filename with store directory prefix
    temp_filename = f"{parent_dir}_{name}_overlay{ext}"
    temp_path = os.path.join(temp_dir, temp_filename)
    
    # Overlay text and return path
    return overlay_text_on_image(img_path, product_name, temp_path)


def scaled_image(img_path, max_w, max_h, maintain_aspect=True):
    """
    Scale image to fit within max dimensions
    Args:
        img_path: Path to image file
        max_w: Maximum width
        max_h: Maximum height
        maintain_aspect: Whether to maintain aspect ratio
    """
    if not img_path or not os.path.exists(img_path):
        # Return placeholder text for missing images
        styles = getSampleStyleSheet()
        return Paragraph("<i>[No Image Available]</i>", styles["Normal"])
    
    try:
        # Get image dimensions
        with PILImage.open(img_path) as pil_img:
            w, h = pil_img.size
        
        if maintain_aspect:
            # Calculate scaling factor
            scale = min(max_w * inch / w, max_h * inch / h)
            return Image(img_path, w * scale, h * scale)
        else:
            # Use exact dimensions
            return Image(img_path, max_w * inch, max_h * inch)
            
    except Exception as e:
        print(f"Error loading image {img_path}: {str(e)}")
        styles = getSampleStyleSheet()
        return Paragraph(f"<i>[Image Error]</i>", styles["Normal"])


def generate_daily_report_pdf(all_stores_data, date_str):
    """
    Generate a single PDF report with all stores for the day
    Layout matches mockup exactly:
    - Header: Store name, Name, Phone, Date
    - Overall photos section (2 images side by side)
    - Product images grid (3 columns)
    
    Args:
        all_stores_data: List of dicts, each containing:
            - meta: dict with store_name, name, phone, date
            - overall_images: list of 2 image paths
            - product_images: list of tuples (product_name, image_path)
        date_str: Date string (YYYY-MM-DD)
    
    Returns:
        Path to the generated PDF
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pdf_path = os.path.join(OUTPUT_DIR, f"Daily_Quality_Report_{date_str}.pdf")
    
    # Create temporary directory for images with overlays
    temp_dir = os.path.join(OUTPUT_DIR, "temp_overlays")
    os.makedirs(temp_dir, exist_ok=True)

    # Setup PDF
    doc = SimpleDocTemplate(
        pdf_path, 
        pagesize=A4,
        topMargin=0.5*inch, 
        bottomMargin=0.5*inch,
        leftMargin=0.5*inch, 
        rightMargin=0.5*inch
    )

    # Setup styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#000000'),
        spaceAfter=8,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'HeaderText',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        alignment=TA_LEFT,
        fontName='Helvetica',
        spaceAfter=0
    )

    elements = []

    # Process each store
    for store_idx, store_data in enumerate(all_stores_data):
        meta = store_data["meta"]
        overall_images = store_data["overall_images"]
        product_images = store_data["product_images"]
        
        # ==================== HEADER SECTION ====================
        # Store name (bold, large)
        elements.append(Paragraph(f"<b>STORE: {meta['store_name']}</b>", title_style))
        
        # Metadata in one line (Name | Phone | Date)
        meta_text = f"<b>Name:</b> {meta['name']} &nbsp;&nbsp;&nbsp; <b>Phone:</b> {meta['phone']} &nbsp;&nbsp;&nbsp; <b>Date:</b> {meta['date']}"
        elements.append(Paragraph(meta_text, header_style))
        
        # Space after header (matching mockup)
        elements.append(Spacer(1, 20))
        
        # ==================== OVERALL PHOTOS SECTION ====================
        if overall_images and len(overall_images) >= 2:
            overall_row = []
            
            # Add first 2 overall images
            for idx in range(2):
                if idx < len(overall_images):
                    img_path = overall_images[idx]
                    overall_row.append(
                        scaled_image(img_path, OVERALL_IMAGE_WIDTH, OVERALL_IMAGE_HEIGHT, maintain_aspect=True)
                    )
                else:
                    # Empty placeholder if less than 2 images
                    overall_row.append("")
            
            # Create table with proper spacing
            overall_table = Table(
                [overall_row], 
                colWidths=[OVERALL_IMAGE_WIDTH*inch + 0.2*inch, OVERALL_IMAGE_WIDTH*inch + 0.2*inch]
            )
            overall_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (0, 0), 0),
                ('RIGHTPADDING', (0, 0), (0, 0), 15),
                ('LEFTPADDING', (1, 0), (1, 0), 15),
                ('RIGHTPADDING', (1, 0), (1, 0), 0),
            ]))
            elements.append(overall_table)
            
            # Space after overall photos (matching mockup)
            elements.append(Spacer(1, 25))
        
        # ==================== PRODUCT IMAGES GRID ====================
        if product_images:
            product_table_data = []
            current_row = []
            
            for product_name, img_path in product_images:
                # Create image with overlay
                overlay_img_path = create_image_with_overlay(img_path, product_name, temp_dir)
                
                # Add to current row
                current_row.append(
                    scaled_image(overlay_img_path, PRODUCT_IMAGE_WIDTH, PRODUCT_IMAGE_HEIGHT, maintain_aspect=True)
                )
                
                # If row is complete (3 images), add to table data
                if len(current_row) == 3:
                    product_table_data.append(current_row)
                    current_row = []
            
            # Add remaining images in incomplete row
            if current_row:
                # Fill remaining cells with empty space
                while len(current_row) < 3:
                    current_row.append("")
                product_table_data.append(current_row)
            
            # Create product table with proper spacing
            if product_table_data:
                # Calculate column widths with padding
                col_width = PRODUCT_IMAGE_WIDTH * inch + 0.15 * inch
                
                product_table = Table(
                    product_table_data, 
                    colWidths=[col_width] * 3,
                    rowHeights=[(PRODUCT_IMAGE_HEIGHT * inch + 0.15 * inch)] * len(product_table_data)
                )
                product_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    # Horizontal spacing between columns
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    # Vertical spacing between rows
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ]))
                elements.append(product_table)
        
        # Add page break after each store (except the last one)
        if store_idx < len(all_stores_data) - 1:
            elements.append(PageBreak())

    # Build PDF
    doc.build(elements)
    
    # Clean up temporary overlay images
    try:
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Warning: Could not clean up temp directory: {str(e)}")
    
    return pdf_path