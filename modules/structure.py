import os
import logging
from bs4 import BeautifulSoup

def run(content_dir):
    """
    Applies structural changes to Image containers using BeautifulSoup.
    """
    logging.info(f"Applying structure updates in {content_dir}...")
    
    for root, _, files in os.walk(content_dir):
        for file in files:
            if not (file.endswith('.xhtml') or file.endswith('.html')):
                continue
                
            file_path = os.path.join(root, file)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            soup = BeautifulSoup(content, 'html.parser')
            modified = False

            # RULE 1 & 2 Combined Logic: Find divs containing Inline-Figure
            # Logic:
            # Look for div.Inline-Figure
            # Check parent. If parent is a naked div, we might need to apply class "Figura" to it.
            # Check siblings or inner img.
            
            # The user wants:
            # CASE A:
            # <div class="Inline-Figure">
            #   <div class="Inline-Figure...">
            #     <img ...>
            # BECOMES: parent gets class="Figura", img gets class="figmed"
            
            # CASE B:
            # <div class="Inline-Figure">
            #   <img src=...>
            # BECOMES: div gets class="Inline-Figure ec esq", img gets class="figmed"
            
            # Let's iterate over all divs with class "Inline-Figure"
            # Note: "Inline-Figure" might be a prefix? regex used `class="Inline-Figure(.*?)"`
            # For strict matching, we look for "Inline-Figure" in class list.
            
            # We need to be careful not to process the same elements multiple times if nested.
            # But the structure implies hierarchy.
            
            # Strategy: Find all imgs. Check their parents.
            
            imgs = soup.find_all('img')
            for img in imgs:
                parent = img.find_parent('div')
                if not parent:
                    continue
                
                parent_classes = parent.get('class', [])
                
                # Check if parent is "Inline-Figure" or starts with it?
                # The user regex: <div class="Inline-Figure(.*?)"> matches things like "Inline-Figure-1" too.
                # BS4 separates classes by space. If the class is "Inline-Figure-1", it's a single class.
                # If it is "Inline-Figure something", it's two classes.
                
                is_inline_figure_parent = False
                for cls in parent_classes:
                    if cls.startswith('Inline-Figure'):
                        is_inline_figure_parent = True
                        break
                
                if not is_inline_figure_parent:
                    continue
                    
                # We found an image inside a div.Inline-Figure*
                
                # Check Grandparent
                grandparent = parent.find_parent('div')
                
                # Identify Case A vs Case B
                
                # CASE A: Parent is Inline-Figure*, Grandparent is Inline-Figure, Great-Grandparent is div (naked?)
                # Wait, regex 1:
                # <div>
                #   <div class="Inline-Figure">
                #     <div class="Inline-Figure(.*?)">   <-- Parent
                #       <img ...>                        <-- Img
                
                if grandparent:
                    grandparent_classes = grandparent.get('class', [])
                    if 'Inline-Figure' in grandparent_classes:
                        # This matches Case A structure
                        great_grandparent = grandparent.find_parent('div')
                        if great_grandparent:
                            # Apply "Figura" to Great-Grandparent
                            # User regex: <div class="Figura"> (replacing <div>)
                            if 'Figura' not in great_grandparent.get('class', []):
                                great_grandparent['class'] = great_grandparent.get('class', []) + ['Figura']
                                modified = True
                            
                            # Add class "figmed" to img
                            if 'figmed' not in img.get('class', []):
                                img['class'] = img.get('class', []) + ['figmed']
                                modified = True
                                
                        continue # Done with this img
                        
                # CASE B:
                # <div>
                #   <div class="Inline-Figure">   <-- Parent
                #     <img src=...>               <-- Img
                
                # If we are here, it didn't match Case A (nested Inline-Figure).
                # So Parent is Inline-Figure.
                if 'Inline-Figure' in parent_classes:
                    # Modify Parent classes: add "ec" "esq"
                    # regex: <div class="Inline-Figure ec esq">
                    
                    if 'ec' not in parent_classes:
                        parent['class'].append('ec')
                    if 'esq' not in parent_classes:
                        parent['class'].append('esq')
                        
                    # Add class "figmed" to img
                    if 'figmed' not in img.get('class', []):
                        img['class'] = img.get('class', []) + ['figmed']
                    
                    modified = True

            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                    logging.debug(f"Structured {file} (BS4)")
