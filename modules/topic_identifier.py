import os
import requests
import logging
import json
from bs4 import BeautifulSoup
from config import Config

def analyze_table_with_ai(rows_text):
    """
    Sends the entire table content to LM Studio to identify topic rows.
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
        "Return ONLY a JSON array of integers containing the row numbers (indices) of the topic headers.\n"
        "Example: [0, 5]\n"
        "If no topics are found, return: []\n"
        "Do not write explanations."
    )
    
    payload = {
        "messages": [
            {"role": "system", "content": "Return only a JSON array."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 100
    }
    
    print(f"  [AI] Analyzing Table ({len(rows_text)} rows)... ", end="", flush=True)
    
    try:
        response = requests.post(Config.LM_STUDIO_URL, json=payload, timeout=20)
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content'].strip()
            
            # Cleaning up common LLM artifacts
            content = content.replace("```json", "").replace("```", "").strip()
            
            # Try to find list brackets
            start = content.find('[')
            end = content.rfind(']') + 1
            
            if start != -1 and end != -1:
                json_str = content[start:end]
                try:
                    indices = json.loads(json_str)
                    print(f"-> Detected Topics at indices: {indices}")
                    return indices
                except json.JSONDecodeError:
                    print(f"-> JSON Error: {content}")
            else:
                 print(f"-> Invalid Format: {content[:50]}...")
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
