import os
import logging
from bs4 import BeautifulSoup

def run(content_dir, opf_path):
    """
    Generates a TOC.ncx for ePub based on the files in the OPF spine.
    Ensures the NCX identifier matches the OPF identifier.
    """
    logging.info("Updating/Generating NCX...")
    
    if not os.path.exists(opf_path):
        logging.error(f"OPF file not found at {opf_path}")
        return

    with open(opf_path, 'r', encoding='utf-8') as f:
        opf_soup = BeautifulSoup(f.read(), 'xml')

    # 1. Extract Identifier
    # The unique-identifier attribute in <package> points to the id of the <dc:identifier>
    package_tag = opf_soup.find('package')
    unique_id_ref = package_tag.get('unique-identifier') if package_tag else None
    book_id = "urn:uuid:12345678-1234-1234-1234-123456789012" # Fallback
    
    if unique_id_ref:
        id_tag = opf_soup.find('dc:identifier', id=unique_id_ref)
        if id_tag:
            book_id = id_tag.get_text().strip()
    else:
        # Just grab the first dc:identifier if no unique-identifier ref
        id_tag = opf_soup.find('dc:identifier')
        if id_tag:
            book_id = id_tag.get_text().strip()

    # 2. Extract Title
    title_tag = opf_soup.find('dc:title')
    book_title = title_tag.get_text().strip() if title_tag else "ePub Automation"

    # 3. Identify NCX path and Spine items
    manifest = opf_soup.find('manifest')
    spine = opf_soup.find('spine')
    
    if not manifest or not spine:
        logging.error("Manifest or Spine missing in OPF.")
        return

    # Find existing NCX in manifest
    existing_ncx_item = manifest.find('item', **{'media-type': 'application/x-dtbncx+xml'})
    if existing_ncx_item:
        href = existing_ncx_item.get('href')
        ncx_path = os.path.join(os.path.dirname(opf_path), href)
    else:
        ncx_path = os.path.join(os.path.dirname(opf_path), 'toc.ncx')
        logging.info(f"NCX not found in manifest, using default path: {ncx_path}")

    # Build Spine list (ID -> Href)
    manifest_items = {item.get('id'): item.get('href') for item in manifest.find_all('item')}
    spine_items = [itemref.get('idref') for itemref in spine.find_all('itemref')]

    # 4. Build NCX Content
    ncx_content = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">',
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">',
        '  <head>',
        f'    <meta name="dtb:uid" content="{book_id}" />',
        '    <meta name="dtb:depth" content="1" />',
        '    <meta name="dtb:totalPageCount" content="0" />',
        '    <meta name="dtb:maxPageNumber" content="0" />',
        '  </head>',
        '  <docTitle>',
        f'    <text>{book_title}</text>',
        '  </docTitle>',
        '  <navMap>'
    ]
    
    play_order = 1
    for idref in spine_items:
        href = manifest_items.get(idref)
        if not href:
            continue
            
        # Skip non-HTML files in navMap if necessary, but spine usually only has content
        if not (href.endswith('.xhtml') or href.endswith('.html')):
            continue

        label = os.path.basename(href).replace('.xhtml', '').replace('.html', '')
        
        ncx_content.append(f'    <navPoint id="navPoint-{play_order}" playOrder="{play_order}">')
        ncx_content.append(f'      <navLabel><text>{label}</text></navLabel>')
        ncx_content.append(f'      <content src="{href}" />')
        ncx_content.append(f'    </navPoint>')
        play_order += 1
        
    ncx_content.append('  </navMap>')
    ncx_content.append('</ncx>')
    
    with open(ncx_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(ncx_content))
    
    logging.info(f"NCX generated successfully with identifier: {book_id}")

