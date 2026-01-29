import os
import re
import logging
from bs4 import BeautifulSoup
from config import Config

def invert_attributes(html_content):
    """
    Inverts the order of 'id' and 'class' attributes in HTML tags.
    Ensures 'class' comes *before* 'id' to satisfy the strict regex requirements.
    
    Target: <tag ... id="..." class="..." ...> -> <tag ... class="..." id="..." ...>
    """
    # Regex to capture:
    # Group 1: opening of tag and potential other attributes matching [^>]*
    # Group 2: id attribute
    # Group 3: whitespace/intervening chars
    # Group 4: class attribute
    # Note: This is a robust-enough approximation for standard XML/HTML.
    
    pattern = re.compile(r'(<[^>]+)\s+(id="[^"]*")(\s+)(class="[^"]*")', re.IGNORECASE)
    
    # Replacement: Group 1 + whitespace + Group 4 (class) + Group 3 + Group 2 (id)
    # We add a space after Group 1 just in case, but usually \s+ handles it.
    
    return pattern.sub(r'\1 \4\3\2', html_content)

def clean_h1_in_lists(content, pattern_info):
    """
    Removes h1/h2 tags nested inside lists (ul/ol) which is invalid/messy HTML.
    Uses the pattern from config.
    """
    regex = pattern_info['pattern']
    # The users regex uses backreferences \1 to match content.
    # We try to apply it safely.
    
    try:
        # Note: Users regex: <h2 ...>(.*?)</h2></li>...</ul>...\1</h2>
        # This implies it pulls the content out of the list and reconstructs the h2.
        return re.sub(regex, r'<h2 class="_1-Titulo-1">\1</h2>', content, flags=re.DOTALL)
    except Exception as e:
        logging.warning(f"Error applying H1 list cleaning: {e}")
        return content

def move_headers_out_of_lists(soup):
    """
    Finds header tags (h1-h6) nested inside <li> tags and moves them 
    outside the parent list (ul/ol).
    """
    modified = False
    # Find all h1, h2, h3, h4, h5, h6 tags
    headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    
    for h in headers:
        # Check if the header is inside an li
        li_parent = h.find_parent('li')
        if li_parent:
            # Found a nested header. We need to move it out of the list.
            # Usually it's at the end of the li, but let's be safe.
            
            # Find the root list container (ul or ol)
            list_container = li_parent.find_parent(['ul', 'ol'])
            if list_container:
                # Move the header after the list container
                h_extract = h.extract()
                list_container.insert_after(h_extract)
                modified = True
                logging.info(f"Moved header '{h_extract.get_text()[:20]}...' out of list.")
                
    return modified

def run(content_dir):
    logging.info(f"Cleaning files in {content_dir}...")
    
    for root, _, files in os.walk(content_dir):
        for file in files:
            if file.endswith('.xhtml') or file.endswith('.html'):
                file_path = os.path.join(root, file)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # 1. Attribute Normalization (Class before ID)
                content = invert_attributes(content)
                
                # 2. General Regex Cleaning (from Config)
                for pattern in Config.REGEX_REMOVE_PATTERNS:
                    # Replace with empty string
                    content = re.sub(pattern, '', content)
                    
                # 3. H1 inside Lists
                content = clean_h1_in_lists(content, Config.REGEX_H1_UL_FIX)
                
                # 4. Remove Empty Divs
                # Pattern: <div>\s*<div class="Basic-Text-Frame"></div>\s*</div>
                content = re.sub(r'<div>\s*<div class="Basic-Text-Frame"></div>\s*</div>', '', content)
                
                # 5. Fix Nested Headers using BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                if move_headers_out_of_lists(soup):
                    content = str(soup)

                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logging.debug(f"Cleaned {file}")
