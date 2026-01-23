import os
import logging
from PIL import Image
from pyzbar.pyzbar import decode

def run(content_dir):
    """
    Scans images in the content directory for QR codes,
    logs them, and creates a summary report.
    """
    logging.info(f"Scanning for QR codes in {content_dir}...")

    report_entries = []
    
    # Supported image extensions
    image_extensions = ('.png', '.jpg', '.jpeg', '.webp')

    for root, _, files in os.walk(content_dir):
        for file in files:
            if file.lower().endswith(image_extensions):
                file_path = os.path.join(root, file)
                try:
                    with Image.open(file_path) as img:
                        decoded_objects = decode(img)
                        for obj in decoded_objects:
                            qr_data = obj.data.decode("utf-8")
                            qr_type = obj.type
                            
                            # Only interested in QR codes, but pyzbar might find barcodes too.
                            # The user specifically asked for QR Code identifier.
                            if qr_type == 'QRCODE':
                                logging.info(f"QR Code found in {file}: {qr_data}")
                                report_entries.append((file, qr_data))
                except Exception as e:
                    logging.warning(f"Could not scan image {file}: {e}")

    if report_entries:
        report_path = os.path.join(os.path.dirname(content_dir), "qr_code_report.txt")
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
