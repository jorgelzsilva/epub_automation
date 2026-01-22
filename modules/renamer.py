import os
import re
import logging

def run(content_dir, opf_path):
    """
    Renames *artigo*.xhtml files to artigo1.xhtml, artigo2.xhtml, etc.
    Updates the OPF manifest to reflect strict changes.
    """
    logging.info(f"Scanning for article files in {content_dir}...")
    
    files = []
    # Only look for XHTML files in the same dir as OPF (usually OEBPS/Text or OEBPS)
    # The OPF often lives in OEBPS, and text in OEBPS/Text, or everything in OEBPS.
    # We should search recursively from content_dir or just assume standard structure?
    # Let's search recursively but filter carefully.
    
    # However, renames must match what's in the OPF manifest.
    # It's safer to read the OPF first to find the files that need renaming.
    
    with open(opf_path, 'r', encoding='utf-8') as f:
        opf_content = f.read()

    # Regex to find item hrefs that look like articles.
    # Format: <item id="..." href="Text/NomeDoArtigo.xhtml" media-type="..." />
    # We are looking for files ending in *artigo*.xhtml (case insensitive)
    # The user said: "...artigo.xhtml, ...artigo1.xhtml ... starts in artigo1.xhtml"
    
    # Strategy:
    # 1. Find all files in the filesystem that match the pattern.
    # 2. Sort them (hopefully they have some order or we trust filesystem order? User indicated "doing stages", implies manual/visual order?)
    #    If they are named "01-artigo.xhtml", "02-artigo.xhtml", sorting works.
    #    If random names, order might be lost. 
    #    Let's rely on alphanumeric sort of existing filenames.
    
    found_files = []
    for root, _, filenames in os.walk(content_dir):
        for name in filenames:
            if name.lower().endswith('.xhtml') and 'artigo' in name.lower():
                full_path = os.path.join(root, name)
                # Keep rel path to content_dir for OPF matching
                rel_path = os.path.relpath(full_path, content_dir).replace('\\', '/')
                found_files.append((full_path, rel_path, name))
                
    # Sort files to ensure 1, 2, 3...
    found_files.sort(key=lambda x: x[2])
    
    renaming_map = {} # old_rel_path -> new_rel_path
    
    for idx, (full_path, rel_path, name) in enumerate(found_files, 1):
        # Determine new name
        # Replace "artigo" (case insensitive) with "artigo{idx}" before .xhtml
        # e.g., epub-PROAPSI-C2V1_Artigo.xhtml -> epub-PROAPSI-C2V1_Artigo1.xhtml
        
        import re
        repl = r'\g<1>' + str(idx) + r'\g<2>'
        new_filename = re.sub(r'(artigo)(\.xhtml)$', repl, name, flags=re.IGNORECASE)
        folder = os.path.dirname(rel_path)
        new_rel_path = f"{folder}/{new_filename}" if folder else new_filename
        
        new_full_path = os.path.join(os.path.dirname(full_path), new_filename)
        
        if full_path != new_full_path:
            # Rename file
            try:
                os.rename(full_path, new_full_path)
                renaming_map[rel_path] = new_rel_path
                logging.info(f"Renamed: {rel_path} -> {new_rel_path}")
            except OSError as e:
                logging.error(f"Failed to rename {rel_path}: {e}")
        
    # Update OPF content
    if renaming_map:
        new_opf_content = opf_content
        for old_rel, new_rel in renaming_map.items():
            # Replace href="old_rel" with href="new_rel"
            # Be careful with partial matches. Include quotes.
            # Also url encoded paths could exist.
            
            # Simple replacement
            new_opf_content = new_opf_content.replace(f'href="{old_rel}"', f'href="{new_rel}"')
            
        with open(opf_path, 'w', encoding='utf-8') as f:
            f.write(new_opf_content)
            
    # Update TOC (toc.xhtml or nav.xhtml) if it exists
    if renaming_map:
        toc_paths = []
        for root, _, filenames in os.walk(content_dir):
            for name in filenames:
                if name.lower() in ['toc.xhtml', 'nav.xhtml']:
                    toc_paths.append(os.path.join(root, name))
        
        for toc_path in toc_paths:
            with open(toc_path, 'r', encoding='utf-8') as f:
                toc_content = f.read()
            
            new_toc_content = toc_content
            for old_rel, new_rel in renaming_map.items():
                # Replace the filename in hrefs, not the full path
                old_filename = os.path.basename(old_rel)
                new_filename = os.path.basename(new_rel)
                new_toc_content = new_toc_content.replace(old_filename, new_filename)
                
            with open(toc_path, 'w', encoding='utf-8') as f:
                f.write(new_toc_content)
            logging.info(f"Updated TOC: {toc_path}")
    
    return renaming_map
