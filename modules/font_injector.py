import os
import shutil
import logging
from bs4 import BeautifulSoup

def run(content_dir, opf_path):
    """
    Injects fonts from assets/fonts into the EPUB and updates the OPF manifest.
    """
    logging.info("Injecting fonts...")
    
    # 1. Define paths
    # assets/fonts is at the root of the project
    assets_fonts_dir = os.path.join(os.getcwd(), 'assets', 'fonts')
    # target fonts dir in the extracted EPUB content dir
    target_fonts_dir = os.path.join(content_dir, 'Fonts')
    
    if not os.path.exists(assets_fonts_dir):
        logging.warning(f"Assets fonts directory not found: {assets_fonts_dir}")
        return

    if not os.path.exists(target_fonts_dir):
        os.makedirs(target_fonts_dir)
        logging.info(f"Created directory: {target_fonts_dir}")

    # 2. Copy fonts
    fonts_copied = []
    for font_file in os.listdir(assets_fonts_dir):
        if font_file.lower().endswith(('.ttf', '.otf', '.woff', '.woff2')):
            src = os.path.join(assets_fonts_dir, font_file)
            dst = os.path.join(target_fonts_dir, font_file)
            shutil.copy2(src, dst)
            fonts_copied.append(font_file)
            logging.debug(f"Copied font: {font_file}")

    if not fonts_copied:
        logging.info("No fonts found to copy.")
        return

    logging.info(f"Copied {len(fonts_copied)} fonts to {target_fonts_dir}")

    # 3. Update OPF Manifest
    update_opf_manifest(opf_path, fonts_copied)

def update_opf_manifest(opf_path, fonts_copied):
    """
    Adds copied fonts to the <manifest> in the OPF file.
    """
    with open(opf_path, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'xml') # Use xml parser for OPF
    manifest = soup.find('manifest')
    
    if not manifest:
        logging.error("Could not find <manifest> in OPF file.")
        return

    # Check existing items to avoid duplicates
    existing_hrefs = [item.get('href') for item in manifest.find_all('item')]
    
    modified = False
    for font_file in fonts_copied:
        # Expected path in EPUB is usually relative to the OPF file
        # Since content_dir is os.path.dirname(opf_path), 
        # and fonts are in content_dir/Fonts, the href should be 'Fonts/filename'
        font_href = f"Fonts/{font_file}"
        
        if font_href in existing_hrefs:
            logging.debug(f"Font already in manifest: {font_href}")
            continue
            
        # Determine media type
        ext = os.path.splitext(font_file)[1].lower()
        if ext == '.ttf':
            media_type = "font/ttf"
        elif ext == '.otf':
            media_type = "font/otf"
        elif ext == '.woff':
            media_type = "font/woff"
        elif ext == '.woff2':
            media_type = "font/woff2"
        else:
            media_type = "application/octet-stream"

        # Create new item
        # ID should be unique. Using filename as base.
        item_id = font_file.replace('.', '_').replace('-', '_')
        
        new_item = soup.new_tag('item', 
                                id=item_id, 
                                href=font_href, 
                                **{'media-type': media_type})
        manifest.append(new_item)
        modified = True
        logging.info(f"Added {font_file} to manifest.")

    if modified:
        with open(opf_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        logging.info("OPF manifest updated with new fonts.")
