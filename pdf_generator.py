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


# add text overlay on image
def overlay_text_on_image(image_path, text, output_path):
    try:
        img = cv2.imread(image_path)
        if img is None:
            return image_path
        
        h, w = img.shape[:2]
        overlay = img.copy()
        bar_height = int(h * 0.12)
        
        cv2.rectangle(overlay, (0, h - bar_height), (w, h), (0, 0, 0), -1)
        
        
        alpha = 0.35  
        img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = min(w, h) / 500
        font_thickness = max(1, int(font_scale * 2))
        
        (text_width, text_height), _ = cv2.getTextSize(
            text, font, font_scale, font_thickness
        )
        
        text_x = (w - text_width) // 2
        text_y = h - (bar_height // 2) + (text_height // 2)
        
        cv2.putText(
            img, text, (text_x, text_y), font,
            font_scale, (255, 255, 255), font_thickness, cv2.LINE_AA
        )
        
        cv2.imwrite(output_path, img)
        return output_path
        
    except Exception as e:
        print(f"Error overlaying text on {image_path}: {str(e)}")
        return image_path


# create image with product name overlay
def create_image_with_overlay(img_path, product_name, temp_dir):
    if not os.path.exists(img_path) or img_path == PLACEHOLDER_IMAGE:
        return img_path
    
    os.makedirs(temp_dir, exist_ok=True)
    
    parent_dir = os.path.basename(os.path.dirname(img_path))
    filename = os.path.basename(img_path)
    name, ext = os.path.splitext(filename)
    
    temp_filename = f"{parent_dir}_{name}_overlay{ext}"
    temp_path = os.path.join(temp_dir, temp_filename)
    
    return overlay_text_on_image(img_path, product_name, temp_path)


# resize image for pdf
def scaled_image(img_path, max_w, max_h, maintain_aspect=True):
    if not img_path or not os.path.exists(img_path):
        styles = getSampleStyleSheet()
        return Paragraph("<i>[No Image Available]</i>", styles["Normal"])
    
    try:
        with PILImage.open(img_path) as pil_img:
            w, h = pil_img.size
        
        if maintain_aspect:
            scale = min(max_w * inch / w, max_h * inch / h)
            return Image(img_path, w * scale, h * scale)
        else:
            return Image(img_path, max_w * inch, max_h * inch)
            
    except Exception as e:
        print(f"Error loading image {img_path}: {str(e)}")
        styles = getSampleStyleSheet()
        return Paragraph(f"<i>[Image Error]</i>", styles["Normal"])


# generate daily pdf report
def generate_daily_report_pdf(all_stores_data, date_str):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pdf_path = os.path.join(OUTPUT_DIR, f"Daily_Quality_Report_{date_str}.pdf")
    
    temp_dir = os.path.join(OUTPUT_DIR, "temp_overlays")
    os.makedirs(temp_dir, exist_ok=True)

    doc = SimpleDocTemplate(
        pdf_path, 
        pagesize=A4,
        topMargin=0.5*inch, 
        bottomMargin=0.5*inch,
        leftMargin=0.5*inch, 
        rightMargin=0.5*inch
    )

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

    for store_idx, store_data in enumerate(all_stores_data):
        meta = store_data["meta"]
        overall_images = store_data["overall_images"]
        product_images = store_data["product_images"]
        
        elements.append(Paragraph(f"<b>STORE: {meta['store_name']}</b>", title_style))
        
        meta_text = f"<b>Name:</b> {meta['name']} &nbsp;&nbsp;&nbsp; <b>Phone:</b> {meta['phone']} &nbsp;&nbsp;&nbsp; <b>Date:</b> {meta['date']}"
        elements.append(Paragraph(meta_text, header_style))
        elements.append(Spacer(1, 20))
        
        if overall_images and len(overall_images) >= 2:
            overall_row = []
            for idx in range(2):
                if idx < len(overall_images):
                    img_path = overall_images[idx]
                    overall_row.append(
                        scaled_image(img_path, OVERALL_IMAGE_WIDTH, OVERALL_IMAGE_HEIGHT, maintain_aspect=True)
                    )
                else:
                    overall_row.append("")
            
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
            elements.append(Spacer(1, 25))
        
        if product_images:
            product_table_data = []
            current_row = []
            
            for product_name, img_path in product_images:
                overlay_img_path = create_image_with_overlay(img_path, product_name, temp_dir)
                
                current_row.append(
                    scaled_image(overlay_img_path, PRODUCT_IMAGE_WIDTH, PRODUCT_IMAGE_HEIGHT, maintain_aspect=True)
                )
                
                if len(current_row) == 3:
                    product_table_data.append(current_row)
                    current_row = []
            
            if current_row:
                while len(current_row) < 3:
                    current_row.append("")
                product_table_data.append(current_row)
            if product_table_data:
                col_width = PRODUCT_IMAGE_WIDTH * inch + 0.15 * inch
                
                product_table = Table(
                    product_table_data, 
                    colWidths=[col_width] * 3,
                    rowHeights=[(PRODUCT_IMAGE_HEIGHT * inch + 0.15 * inch)] * len(product_table_data)
                )
                product_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ]))
                elements.append(product_table)
        
        if store_idx < len(all_stores_data) - 1:
            elements.append(PageBreak())

    doc.build(elements)

    try:
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Warning: Could not clean up temp directory: {str(e)}")
    
    return pdf_path
