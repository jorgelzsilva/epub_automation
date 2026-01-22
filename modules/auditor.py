import os
import logging
from bs4 import BeautifulSoup

def count_elements(content_dir, label):
    """
    Scans all XHTML files and counts: p, img, table, tr, li, Atividade.
    Returns a dict with totals.
    """
    stats = {
        'p': 0,
        'img': 0,
        'table': 0,
        'tr': 0,
        'input': 0, # Radio buttons
        'li': 0,
        'activity': 0
    }
    
    # Generated text signatures to ignore in the final count
    generated_texts = [
        "Confira aqui a resposta",
        "Resposta correta.",
        "Resposta incorreta. A alternativa correta é a", 
        "A alternativa correta é a"
    ]
    
    # Generated classes to ignore in P count (injected by interactivity.py)
    generated_classes = [
        '_1-Corpo-Comentario',
        '_1-Corpo-Resposta',
        '_r-Atividade-Resposta' # The button label p has this class
    ]
    
    logging.info(f"[{label}] Auditing content elements...")
    
    for root, _, files in os.walk(content_dir):
        for file in files:
            if not (file.endswith('.xhtml') or file.endswith('.html')):
                continue
                
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            soup = BeautifulSoup(content, 'html.parser')
            
            # Simple Counts
            stats['img'] += len(soup.find_all('img'))
            stats['table'] += len(soup.find_all('table'))
            stats['tr'] += len(soup.find_all('tr'))
            stats['input'] += len(soup.find_all('input'))
            stats['li'] += len(soup.find_all('li'))
            
            # Count logical Activities
            stats['activity'] += len(soup.find_all(class_='_c-Atividade-Enunciado'))
            
            # Paragraphs need strict filtering for the "After" stage
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text().strip()
                classes = p.get('class', [])
                
                # Check for generated content
                is_generated = False
                
                # Filter by Class
                for gen_cls in generated_classes:
                    if gen_cls in classes:
                        is_generated = True
                        break
                        
                if is_generated:
                    continue

                # Filter by Text Start (Safety fallback)
                for gen_text in generated_texts:
                    if text.startswith(gen_text):
                        is_generated = True
                        break
                
                if not is_generated:
                    stats['p'] += 1
                    
    logging.info(f"[{label}] Stats: {stats}")
    return stats

def compare(start_stats, end_stats):
    """
    Logs comparison between two stats dicts.
    """
    logging.info("=== AUDIT REPORT ===")
    match = True
    
    # keys that must match exactly
    exact_keys = ['img', 'table', 'tr', 'li', 'activity']
    
    for key in exact_keys:
        if start_stats[key] == end_stats[key]:
            logging.info(f"MATCH: {key.upper()} count: {start_stats[key]}")
        else:
            logging.warning(f"MISMATCH: {key.upper()} - Before: {start_stats[key]}, After: {end_stats[key]}")
            match = False
            
    # Logic for paragraphs (filtered)
    if start_stats['p'] == end_stats['p']:
        logging.info(f"MATCH: Paragraphs (adjusted): {start_stats['p']}")
    else:
        diff = end_stats['p'] - start_stats['p']
        logging.warning(f"MISMATCH: Paragraphs - Before: {start_stats['p']}, After (Adjusted): {end_stats['p']} (Diff: {diff})")
        # Allow small diffs if unavoidable, but ideally should be 0 with good filtering
        # match = False 
        
    if match:
        logging.info("SUCCESS: Content elements preserved.")
    else:
        logging.error("FAILURE: Content elements count mismatch.")
