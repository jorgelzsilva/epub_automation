import os
import re
import logging
from bs4 import BeautifulSoup

def run(content_dir):
    """
    Finds URLs in the text content within <body> tags of XHTML files
    and wraps them in <a href="url" target="_blank">url</a>
    """
    logging.info("Processing URLs in body content...")
    
    # Regex to match URLs (simple version)
    url_pattern = re.compile(r'(https?://[^\s<>"{}|\\^`\[\]]+)')
    
    count = 0
    for root, _, filenames in os.walk(content_dir):
        for name in filenames:
            if name.lower().endswith('.xhtml'):
                file_path = os.path.join(root, name)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                soup = BeautifulSoup(content, 'html.parser')
                body = soup.body
                if body:
                    # Process text nodes in body
                    for text_node in body.find_all(text=True):
                        if text_node.parent.name not in ['a', 'script', 'style']:  # Avoid processing inside links or scripts
                            new_text = url_pattern.sub(r'<a href="\1" target="_blank">\1</a>', text_node.string)
                            if new_text != text_node.string:
                                text_node.replace_with(BeautifulSoup(new_text, 'html.parser'))
                    
                    # Write back
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(str(soup))
                    count += 1
                    logging.info(f"Processed: {file_path}")
    
    logging.info(f"URL linking completed. Files processed: {count}")