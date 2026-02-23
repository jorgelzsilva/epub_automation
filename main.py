import sys
import os
import argparse
import shutil
import logging
import glob
import time
from config import Config
from utils.epub_wrapper import extract_epub, package_epub
from modules import renamer, cleaner, structure, interactivity, topic_identifier, ncx_generator, auditor, url_linker, qr_scanner, font_injector

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("epub_automation.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def process_file(input_path, output_path, enable_url_linker=True):
    start_single = time.time()
    logging.info(f"Starting processing: {input_path} -> {output_path}")

    # Temporary work directory
    work_dir = os.path.join(os.path.dirname(output_path), f"temp_epub_{os.path.basename(input_path)}")
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)

    ai_metrics = {"total_ai_time": 0, "total_tokens": 0, "ai_calls": 0}

    try:
        # 0. Extract
        opf_path, content_dir = extract_epub(input_path, work_dir)
        logging.info(f"Extracted to {content_dir}, OPF: {opf_path}")

        # AUDIT START
        start_stats = auditor.count_elements(content_dir, "BEFORE")

        # 1. Rename Files (Skipped as per current logic)
        logging.info("Renaming skipped.")

        # 2. Cleaner
        pre_clean_size = sum(os.path.getsize(os.path.join(root, f)) for root, _, files in os.walk(content_dir) for f in files)
        cleaner.run(content_dir)
        post_clean_size = sum(os.path.getsize(os.path.join(root, f)) for root, _, files in os.walk(content_dir) for f in files)
        logging.info(f"Cleaning completed. Size change: {pre_clean_size} -> {post_clean_size} bytes")
        
        # 2.5. QR Scanner
        qr_scanner.run(content_dir, os.getcwd())

        # 3. Structural Changes (Images)
        structure.run(content_dir)
        logging.info("Structure updates completed.")

        # 3.5. Inject Fonts
        font_injector.run(content_dir, opf_path)
        logging.info("Fonts injected.")

        # 4. Interactivity (Plugin Logic)
        interactivity.run(content_dir, opf_path)
        logging.info("Interactivity injected.")

        # 4.5. URL Linker
        if enable_url_linker:
            url_linker.run(content_dir)
            logging.info("URL linking completed.")

        # 5. Topic Identifier (AI)
        ai_metrics = topic_identifier.run(content_dir)
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

        end_single = time.time()
        total_time = end_single - start_single
        
        print(f"\nProcessed {os.path.basename(input_path)} in {total_time:.2f}s")
        if ai_metrics["ai_calls"] > 0:
            avg_ai = ai_metrics["total_ai_time"] / ai_metrics["ai_calls"]
            print(f"AI Stage: {ai_metrics['total_ai_time']:.2f}s (Avg: {avg_ai:.2f}s, Tokens: {ai_metrics['total_tokens']})")

    except Exception as e:
        logging.error(f"Error processing {input_path}: {e}", exc_info=True)
    finally:
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)

def main():
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Automate ePub processing for InteratividadePRO")
    parser.add_argument("--input", help="Path to input ePub or directory (default: input/)")
    parser.add_argument("--output", help="Path to output ePub or directory (default: output/)")
    parser.add_argument("--nolinks", action="store_true", help="Disable URL linking")
    
    args = parser.parse_args()

    enable_url_linker = not args.nolinks
    
    input_arg = args.input or "input"
    output_arg = args.output or "output"

    # Create directories if they don't exist
    if not os.path.exists(input_arg):
        os.makedirs(input_arg)
        logging.info(f"Created input directory: {input_arg}")
    if not os.path.exists(output_arg):
        os.makedirs(output_arg)
        logging.info(f"Created output directory: {output_arg}")

    files_to_process = []
    
    if os.path.isfile(input_arg):
        files_to_process.append(input_arg)
    else:
        files_to_process = glob.glob(os.path.join(input_arg, "*.epub"))

    if not files_to_process:
        logging.info("No .epub files found to process.")
        return

    logging.info(f"Found {len(files_to_process)} files to process.")

    for input_path in files_to_process:
        filename = os.path.basename(input_path)
        # If output is a directory, generate output filename
        if os.path.isdir(output_arg):
            name, ext = os.path.splitext(filename)
            output_path = os.path.join(output_arg, f"{name}_v2{ext}")
        else:
            output_path = output_arg
            
        process_file(input_path, output_path, enable_url_linker)

if __name__ == "__main__":
    main()
