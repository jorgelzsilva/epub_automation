import os
import requests
import logging
import json
from bs4 import BeautifulSoup
from config import Config

import re

def analyze_table_with_ai(rows_text):
    """
    Sends the entire table content to the configured AI provider to identify topic rows.
    Returns a list of integer indices for rows that are topics.
    """
    if not rows_text:
        return []

    # Build a numbered list string for the prompt
    table_str = "\n".join([f"Row {i}: {text[:100]}" for i, text in enumerate(rows_text)])
    
    prompt = (
        "You are an expert document structure analyzer.\n"
        "Your task: Identify rows in the table below that serve as 'Topic Headers', 'Titles', or 'Section Separators'.\n"
        "These are distinct from regular data rows.\n\n"
        "Input Table:\n"
        f"{table_str}\n\n"
        "CRITICAL: Return ONLY a JSON array of integers containing the row numbers (indices) of the topic headers.\n"
        "Example output: [0, 5]\n"
        "If no topics are found, return: []\n"
        "Do not write explanations, introductions, or any other text. Only the JSON array."
    )
    
    payload = {
        "model": Config.AI_MODEL,
        "messages": [
            {"role": "system", "content": "You are a specialized document analyzer that ONLY outputs JSON arrays. Do not reason aloud. Do not explain. Just output the array."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0,
        "max_tokens": 1000  # Increased for models that reason extensively
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    if Config.AI_API_KEY:
        headers["Authorization"] = f"Bearer {Config.AI_API_KEY}"
        
    if Config.AI_PROVIDER == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/jorgelzsilva/epub_automation"
        headers["X-Title"] = "EPUB Automation"

    print(f"  [AI] Analyzing Table ({len(rows_text)} rows) using {Config.AI_PROVIDER}... ", end="", flush=True)
    
    try:
        response = requests.post(Config.AI_API_URL, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message'].get('content', '').strip()
            # Fallback for models that might put the answer in 'reasoning'
            reasoning = data['choices'][0]['message'].get('reasoning', '')
            full_text = content + "\n" + reasoning
            
            # Use regex to find the first bracketed list in the response
            match = re.search(r'\[\s*\d*(?:\s*,\s*\d+)*\s*\]', full_text)
            
            if match:
                json_str = match.group(0)
                try:
                    indices = json.loads(json_str)
                    print(f"-> Detected Topics: {indices}")
                    return indices
                except json.JSONDecodeError:
                    print(f"-> JSON Error in extracted string: {json_str}")
            else:
                 print(f"-> Parsing Error. Raw Response: '{content[:100]}...' [Reasoning len: {len(reasoning)}]")
                 return []
                 
    except Exception as e:
        print(f"-> ERROR ({e})")
        logging.warning(f"AI table check failed: {e}")
        return []
        
    return []

def run(content_dir):
    logging.info(f"Identifying table topics in {content_dir}...")
    
    for root, _, files in os.walk(content_dir):
        for file in files:
            if not (file.endswith('.xhtml') or file.endswith('.html')):
                continue
                
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            soup = BeautifulSoup(content, 'html.parser')
            modified = False
            
            # Find all tables with class 'Quadro-ou-Tabela' (or contain TRs with it?)
            # User previously said: <tr class="Quadro-ou-Tabela">
            # A table might contain multiple such TRs. 
            # We should group them by table to maintain context.
            
            tables = soup.find_all('table')
            
            for table in tables:
                # Optimization: Skip tables that clearly don't have the target class in any way
                # (We will check rows inside)
                
                # Get rows ONLY from tbody if possible to avoid thead titles
                tbody = table.find('tbody')
                if tbody:
                    rows = tbody.find_all('tr')
                else:
                    # Fallback if no tbody, but try to exclude thead
                    thead = table.find('thead')
                    all_rows = table.find_all('tr')
                    if thead:
                        thead_rows = thead.find_all('tr')
                        rows = [r for r in all_rows if r not in thead_rows]
                    else:
                        rows = all_rows
                
                target_rows = []
                target_indices = []
                
                for i, row in enumerate(rows):
                    # Only analyze rows with the specific class "Quadro-ou-Tabela"
                    if 'Quadro-ou-Tabela' not in row.get('class', []):
                        continue
                        
                    text = row.get_text(separator=" ", strip=True)
                    target_rows.append(text)
                    target_indices.append(i)
                    
                if not target_rows:
                    continue

                topic_indices = analyze_table_with_ai(target_rows)
                
                for idx in topic_indices:
                    if isinstance(idx, int) and 0 <= idx < len(target_rows):
                        # Map back to the original row object
                        original_row_index = target_indices[idx]
                        row = rows[original_row_index]
                        
                        classes = row.get('class', [])
                        if 'topico' not in classes:
                            row['class'] = classes + ['topico']
                            modified = True
                            logging.info(f"Marked topic in {file} (Table Row {original_row_index}): {target_rows[idx][:30]}...")

            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
