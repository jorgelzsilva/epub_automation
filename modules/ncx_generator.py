import os
import logging
from utils.epub_wrapper import extract_epub

def run(content_dir, opf_path):
    """
    Generates a generic TOC.ncx for ePub 2 based on the files in the OPF spine.
    This is often required if the input ePub was ePub 3 only or had a broken NCX.
    Sigil generates one automatically; we replicate that behavior.
    """
    logging.info("Updating/Generating NCX...")
    
    # 1. Identify the NCX path from the OPF Manifest
    ncx_path = None
    manifest_items = {}
    spine_items = []
    
    with open(opf_path, 'r', encoding='utf-8') as f:
        opf_lines = f.readlines()
        
    in_manifest = False
    in_spine = False
    
    for line in opf_lines:
        line = line.strip()
        if '<manifest>' in line:
            in_manifest = True
            continue
        if '</manifest>' in line:
            in_manifest = False
        if '<spine' in line:
            in_spine = True
            continue # Warning: spine tag might have attributes
        if '</spine>' in line:
            in_spine = False
            
        if in_manifest:
            # Simple extraction of id and href
            if 'media-type="application/x-dtbncx+xml"' in line:
                # Found existing NCX item
                parts = line.split('href="')
                if len(parts) > 1:
                    href = parts[1].split('"')[0]
                    ncx_path = os.path.join(os.path.dirname(opf_path), href)
                    
        # Collect Manifest Items map (ID -> Href)
        if in_manifest and '<item' in line:
            # Extract ID
            id_start = line.find('id="') + 4
            id_end = line.find('"', id_start)
            item_id = line[id_start:id_end]
            
            # Extract Href
            href_start = line.find('href="') + 6
            href_end = line.find('"', href_start)
            href = line[href_start:href_end]
            
            manifest_items[item_id] = href
            
        # Collect Spine refs
        if in_spine and '<itemref' in line:
            idref_start = line.find('idref="') + 7
            idref_end = line.find('"', idref_start)
            idref = line[idref_start:idref_end]
            spine_items.append(idref)

    if not ncx_path:
        # If not in manifest, assume standard OEBPS/toc.ncx or same dir as OPF
        ncx_path = os.path.join(os.path.dirname(opf_path), 'toc.ncx')
        logging.info(f"NCX not found in manifest, creating at {ncx_path}")
        
    # 2. Build NCX Content
    # We will simply list every file in the spine as a navPoint.
    # Title will be the filename or extracted header if we want to be fancy.
    # For now, filename is robust.
    
    ncx_content = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">',
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">',
        '  <head>',
        '    <meta name="dtb:uid" content="urn:uuid:12345678-1234-1234-1234-123456789012" />',
        '    <meta name="dtb:depth" content="1" />',
        '    <meta name="dtb:totalPageCount" content="0" />',
        '    <meta name="dtb:maxPageNumber" content="0" />',
        '  </head>',
        '  <docTitle>',
        '    <text>ePub Automation</text>',
        '  </docTitle>',
        '  <navMap>'
    ]
    
    play_order = 1
    for item_id in spine_items:
        href = manifest_items.get(item_id)
        if not href:
            continue
            
        # Skip covers or auxiliary files if needed, but usually we want to nav to content.
        # title = href
        
        # Try to find a nice title from the file?
        # Overkill for this stage, use filename.
        label = os.path.basename(href).replace('.xhtml', '')
        
        ncx_content.append(f'    <navPoint id="navPoint-{play_order}" playOrder="{play_order}">')
        ncx_content.append(f'      <navLabel><text>{label}</text></navLabel>')
        ncx_content.append(f'      <content src="{href}" />')
        ncx_content.append(f'    </navPoint>')
        play_order += 1
        
    ncx_content.append('  </navMap>')
    ncx_content.append('</ncx>')
    
    with open(ncx_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(ncx_content))
