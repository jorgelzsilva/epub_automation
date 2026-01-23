import sys
import os
import argparse
import shutil
import logging
from config import Config
from utils.epub_wrapper import extract_epub, package_epub
from modules import renamer, cleaner, structure, interactivity, topic_identifier, ncx_generator, auditor, url_linker, qr_scanner

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("epub_automation.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    parser = argparse.ArgumentParser(description="Automate ePub processing for InteratividadePRO")
    parser.add_argument("input_epub", help="Path to the input ePub file")
    parser.add_argument("output_epub", help="Path to the output ePub file")
    parser.add_argument("--enable-url-linker", action="store_true", help="Enable URL linking in body content")
    
    args = parser.parse_args()

    input_path = os.path.abspath(args.input_epub)
    output_path = os.path.abspath(args.output_epub)

    if not os.path.exists(input_path):
        logging.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logging.info(f"Starting processing: {input_path} -> {output_path}")

    # Temporary work directory
    work_dir = os.path.join(os.path.dirname(output_path), "temp_epub_pro")
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)

    try:
        # 0. Extract
        opf_path, content_dir = extract_epub(input_path, work_dir)
        logging.info(f"Extracted to {content_dir}, OPF: {opf_path}")

        # AUDIT START
        start_stats = auditor.count_elements(content_dir, "BEFORE")

        # 1. Rename Files
        # Returns map of old_name -> new_name to help other modules if needed
        # (though mostly they will just scan the dir again or rely on consistent naming)
        # file_map = renamer.run(content_dir, opf_path)
        logging.info("Renaming skipped by user request.")

        # Reload OPF path if it changed (unlikely for the file itself, but good practice)
        # Note: renamer updates the OPF content, but the file path stays the same relative to work_dir

        # 2. Cleaner (Regex & Attribute Inversion)
        pre_clean_size = sum(os.path.getsize(os.path.join(root, f)) for root, _, files in os.walk(content_dir) for f in files)
        cleaner.run(content_dir)
        post_clean_size = sum(os.path.getsize(os.path.join(root, f)) for root, _, files in os.walk(content_dir) for f in files)
        logging.info(f"Cleaning completed. Size change: {pre_clean_size} -> {post_clean_size} bytes")
        
        # 2.5. QR Scanner
        qr_scanner.run(content_dir)

        # 3. Structural Changes (Images)
        structure.run(content_dir)
        logging.info("Structure updates completed.")

        # 4. Interactivity (Plugin Logic)
        interactivity.run(content_dir)
        logging.info("Interactivity injected.")

        # 4.5. URL Linker (Optional)
        if args.enable_url_linker:
            url_linker.run(content_dir)
            logging.info("URL linking completed.")

        # 5. Topic Identifier (AI)
        # This modifies the files in place
        topic_identifier.run(content_dir)
        logging.info("Topic identification completed.")

        # 6. NCX Generator
        ncx_generator.run(content_dir, opf_path)
        logging.info("NCX updated.")

        # AUDIT END
        end_stats = auditor.count_elements(content_dir, "AFTER")
        auditor.compare(start_stats, end_stats)

        # 7. Package
        package_epub(work_dir, output_path)
        logging.info(f"Successfully created: {output_path}")

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
    finally:
        # Cleanup
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)
            logging.info("Cleaned up temp directory.")

if __name__ == "__main__":
    setup_logging()
    main()
