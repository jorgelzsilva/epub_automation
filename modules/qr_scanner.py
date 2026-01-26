import os
import logging
from PIL import Image
from pyzbar.pyzbar import decode
from bs4 import BeautifulSoup

def run(content_dir, project_root):
    """
    Scans images in the content directory for QR codes,
    wraps them in <a> tags in XHTML files,
    and creates a summary report in the project root.
    """
    logging.info(f"Scanning for QR codes in {content_dir}...")

    # Mapping of absolute image path to its QR content
    image_qr_map = {}
    report_entries = []
    
    # Supported image extensions
    image_extensions = ('.png', '.jpg', '.jpeg', '.webp')

    # Pass 1: Scan all images
    for root, _, files in os.walk(content_dir):
        for file in files:
            if file.lower().endswith(image_extensions):
                file_path = os.path.join(root, file)
                try:
                    # Normalize path for matching
                    abs_path = os.path.abspath(file_path)
                    
                    with Image.open(abs_path) as img:
                        decoded_objects = decode(img)
                        for obj in decoded_objects:
                            qr_data = obj.data.decode("utf-8")
                            qr_type = obj.type
                            
                            if qr_type == 'QRCODE':
                                logging.info(f"QR Code found in {file}: {qr_data}")
                                image_qr_map[abs_path] = qr_data
                                report_entries.append((file, qr_data))
                except Exception as e:
                    logging.warning(f"Could not scan image {file}: {e}")

    # Pass 2: Modify XHTML files
    if image_qr_map:
        logging.info("Modifying XHTML files to link QR codes...")
        modified_files_count = 0
        
        for root, _, files in os.walk(content_dir):
            for file in files:
                if file.lower().endswith('.xhtml'):
                    xhtml_path = os.path.join(root, file)
                    modified = False
                    
                    with open(xhtml_path, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f.read(), 'html.parser')
                    
                    for img in soup.find_all('img'):
                        src = img.get('src')
                        if not src:
                            continue
                        
                        # Resolve src relative to the current xhtml file
                        img_rel_path = os.path.join(os.path.dirname(xhtml_path), src)
                        img_abs_path = os.path.abspath(img_rel_path)
                        
                        if img_abs_path in image_qr_map:
                            qr_url = image_qr_map[img_abs_path]
                            
                            # Check if already wrapped in <a>
                            parent = img.parent
                            if parent and parent.name == 'a':
                                continue
                                
                            # Wrap in <a> tag
                            new_link = soup.new_tag('a', href=qr_url, target="_blank")
                            img.wrap(new_link)
                            modified = True
                            logging.debug(f"Linked QR image {src} in {file}")

                    if modified:
                        with open(xhtml_path, 'w', encoding='utf-8') as f:
                            f.write(str(soup))
                        modified_files_count += 1

        logging.info(f"XHTML modification completed. Files modified: {modified_files_count}")

    # Report Generation
    if report_entries:
        report_path = os.path.join(project_root, "qr_code_report.txt")
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write("QR Code Scan Report\n")
                f.write("===================\n\n")
                for filename, url in report_entries:
                    f.write(f"File: {filename}\n")
                    f.write(f"URL:  {url}\n")
                    f.write("-" * 40 + "\n")
            logging.info(f"QR Code report generated at: {report_path}")
        except Exception as e:
            logging.error(f"Failed to write QR report: {e}")
    else:
        logging.info("No QR codes found.")
