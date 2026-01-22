import os
import re
import logging
import unicodedata
from bs4 import BeautifulSoup
from config import Config

JS_BLOCK = """
<script src='https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js' type='text/javascript'></script>
<script type='text/javascript'>
 //<![CDATA[
 function showMe(par1, par2, par3, par4) {
   document.getElementById(par4).style.display = 'none';
   document.getElementById(par3).style.display = 'none';
   document.getElementById(par2).style.display = 'none';
   document.getElementById(par1).style.display = 'block';
 }
 function showDesdobr(sigla) {
   if (sigla.getElementsByClassName('desdobr')[0].style.display != 'inline') {
      sigla.getElementsByClassName('sigla')[0].style.display = 'none';
      sigla.getElementsByClassName('desdobr')[0].style.display = 'inline';
   } else {
      sigla.getElementsByClassName('sigla')[0].style.display = 'inline';
      sigla.getElementsByClassName('desdobr')[0].style.display = 'none';
   }
 }
$(document).ready(function() {
    $('[class^=Inline-Figure] img').css('cursor', 'pointer');
    $('[class^=Inline-Figure] img').css('max-width', '100%');
    $('[class^=Inline-Figure] img').before('<div class="zoom"></div>');
    $('[class^=Inline-Figure] img').bind('click',function(){
      $(this).parent().toggleClass('InlineGrande');
      $(this).parent().parent().toggleClass('InlineGrande');
      if($('.InlineGrande').is(':visible')) {
        $(this).before('<div class="fundoPreto"></div>');
        $(this).after('<span class="fechar"></span>');
        $('div .zoom').remove();
      } else {
        $('div .fundoPreto').remove();
        $('div .fechar').remove();
        $('[class^=Inline-Figure] img').before('<div class="zoom"></div>');
      }
    });
    $(document).on('click','.zoom',function(){
      $(this).parent().addClass('InlineGrande');
      $(this).parent().parent().addClass('InlineGrande');
      $('.InlineGrande img').before('<div class="fundoPreto"></div>');
      $('.InlineGrande img').after('<span class="fechar"></span>');
      $('div .zoom').remove();
    });
    $(document).on('click', '.fundoPreto, .fechar', function (){
      $('.InlineGrande').removeClass('InlineGrande');
      $('div .fundoPreto').remove();
      $('div .fechar').remove();
      $('[class^=Inline-Figure] img').before('<div class="zoom"></div>');
    });
});
 //]]>
</script>
"""

def normalize_text(text):
    if not text: return ""
    return text.replace('\xa0', ' ').strip()

def strip_accents(text):
    if not text:
        return ""
    nfkd = unicodedata.normalize('NFKD', text)
    without_accents = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    return re.sub(r'\s+', ' ', without_accents).strip()

def clean_html_content(tag_html):
    try:
        soup_temp = BeautifulSoup(tag_html, 'html.parser')
        pattern = re.compile(r'^(Resposta:|Resposta|Comentário:|Comentário)\s*', re.IGNORECASE)
        first_string = soup_temp.find(string=True)
        if first_string:
            cleaned_text = re.sub(pattern, '', first_string)
            first_string.replace_with(cleaned_text)
        return str(soup_temp).strip()
    except:
        return tag_html

def find_tags_with_class(soup, class_name):
    tags = []
    # Using CSS selector is often more robust in bs4 if supported
    # but stick to logic from plugin for consistency
    for tag in soup.find_all(True):
        try:
            classes = tag.get('class')
        except:
            classes = None
        if not classes:
            continue
        if isinstance(classes, (list, tuple)):
            if class_name in classes:
                tags.append(tag)
        else:
            if class_name == classes or class_name in classes:
                tags.append(tag)
    return tags

def run(content_dir):
    logging.info(f"Injecting interactivity in {content_dir}...")
    
    for root, _, files in os.walk(content_dir):
        for file in files:
            if not (file.endswith('.xhtml') or file.endswith('.html')):
                continue
                
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            soup = BeautifulSoup(content, 'html.parser')
            
            # --- LOGIC PORTED FROM PLUGIN.PY ---
            
            gabarito_map = {}
            current_activity = None
            found_gabarito_header = False
            
            # Find all potential relevant tags
            all_elements = soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'li', 'span'])
            to_remove = []
            
            # Pass 1: Build Gabarito Map
            for el in all_elements:
                text_pure = normalize_text(el.get_text())
                norm_for_match = strip_accents(text_pure).lower()
                
                # Check for Gabarito Header
                if el.name in ['h1', 'h2', 'h3', 'h4'] and re.search(r"\b(respostas?\s.*atividades|atividades\s.*respostas?)\b", norm_for_match):
                    found_gabarito_header = True
                    
                if found_gabarito_header:
                    to_remove.append(el)
                    
                # Stop removal if we hit References/Bibliography
                if el.name in ['h1', 'h2', 'h3', 'h4']:
                    if re.search(r'^(referencias|referencia|bibliografia|leitura)', norm_for_match):
                        current_activity = None
                        if el in to_remove: to_remove.remove(el)
                        found_gabarito_header = False
                        continue
                
                # Identify Activity Number
                act_match = re.match(r'^Atividade[:\s]*0*(\d+)', text_pure, re.IGNORECASE)
                if act_match:
                    current_activity = act_match.group(1)
                    if current_activity not in gabarito_map:
                        gabarito_map[current_activity] = {'resposta': '', 'comentario': ''}
                elif current_activity:
                    # Capture Response/Comment
                    try:
                        inner_html = el.decode_contents()
                    except:
                        inner_html = el.get_text()
                        
                    if re.match(r'^Resposta:|^Resposta\b', text_pure, re.IGNORECASE):
                        gabarito_map[current_activity]['resposta'] = clean_html_content(inner_html)
                    elif re.match(r'^Comentário:|^Comentário\b', text_pure, re.IGNORECASE):
                        gabarito_map[current_activity]['comentario'] = clean_html_content(inner_html)
                    elif gabarito_map[current_activity]['comentario'] and not re.match(r'^Atividade', text_pure, re.IGNORECASE):
                        gabarito_map[current_activity]['comentario'] += ' ' + inner_html.strip()

            # Note: We do NOT decompose the gabarito tags as per the original script comment:
            # "Não decompor (remover) as tags do gabarito"
            
            # Pass 2: Apply Interactivity to Enunciados
            enunciados = find_tags_with_class(soup, "_c-Atividade-Enunciado")
            
            for enunciado in enunciados:
                text_enunciado = normalize_text(enunciado.get_text())
                match_num = re.match(r'^0*(\d+)[\.\)]', text_enunciado)
                
                if match_num:
                    num = match_num.group(1)
                    dados = gabarito_map.get(num)
                    
                    if dados:
                        # IDs
                        idE = "opc" + num + "E"
                        idC = "opc" + num + "C"
                        idR = "opc" + num + "R"
                        idD = "opc" + num + "D"
                        
                        current = enunciado.find_next_sibling()
                        is_multipla = False
                        
                        while current:
                            if isinstance(current, str) or current.name is None:
                                current = current.find_next_sibling()
                                continue
                                
                            classes = current.get('class', [])
                            
                            # Multiple Choice Interaction
                            if '_b-Atividade-alternativa' in classes:
                                is_multipla = True
                                alt_text = normalize_text(current.get_text())
                                letra_match = re.match(r'^([A-Da-d])[\)\.]', alt_text)
                                
                                if letra_match:
                                    letra = letra_match.group(1).lower()
                                    # Extract correct letter from response HTML
                                    resp_soup_temp = BeautifulSoup(dados['resposta'], 'html.parser')
                                    letra_correta_raw = resp_soup_temp.get_text().strip()
                                    letra_correta = letra_correta_raw[0].lower() if letra_correta_raw else ""
                                    
                                    is_correct = (letra == letra_correta)
                                    onclick = f"showMe('{idC}', '{idE}', '{idR}', '{idD}')" if is_correct else f"showMe('{idE}', '{idC}', '{idR}', '{idD}')"
                                    
                                    if not current.find('input'):
                                        new_radio = soup.new_tag('input')
                                        new_radio['type'] = "radio"
                                        new_radio['name'] = "opc"+num
                                        new_radio['value'] = letra
                                        new_radio['onclick'] = onclick
                                        current.insert(0, new_radio)
                            
                            # Answer Button and Feedback Divs
                            if '_r-Atividade-Resposta' in classes:
                                # Create Button
                                div_btn = soup.new_tag('div', id=idR)
                                div_btn['onclick'] = f"showMe('{idD}', '{idE}', '{idR}', '{idC}')"
                                p_btn = soup.new_tag('p')
                                p_btn['class'] = '_r-Atividade-Resposta'
                                p_btn.string = "Confira aqui a resposta"
                                div_btn.append(p_btn)
                                
                                # Prepare HTML contents
                                com_html = BeautifulSoup(dados['comentario'], 'html.parser')
                                res_html = BeautifulSoup(dados['resposta'], 'html.parser')

                                # 1. Error Div
                                div_erro = soup.new_tag('div')
                                div_erro['class'] = 'questaoErrada'
                                div_erro['id'] = idE
                                if is_multipla:
                                    p_res_inc = soup.new_tag('p')
                                    p_res_inc['class'] = '_1-Corpo-Resposta'
                                    p_res_inc.append('Resposta incorreta. A alternativa correta é a "')
                                    p_res_inc.append(BeautifulSoup(str(res_html), 'html.parser'))
                                    p_res_inc.append('".')
                                    div_erro.append(p_res_inc)
                                
                                hr_tag = soup.new_tag('hr', **{'class': 'resposta'})
                                div_erro.append(hr_tag)
                                p_com_erro = soup.new_tag('p')
                                p_com_erro['class'] = '_1-Corpo-Comentario'
                                if com_html.get_text(strip=True):
                                    p_com_erro.append(BeautifulSoup(str(com_html), 'html.parser'))

                                div_erro.append(p_com_erro)

                                # 2. Correct Div
                                div_acerto = soup.new_tag('div')
                                div_acerto['class'] = 'questaoCorreta'
                                div_acerto['id'] = idC
                                p_res_corr = soup.new_tag('p')
                                p_res_corr['class'] = '_1-Corpo-Resposta'
                                p_res_corr.string = "Resposta correta."
                                div_acerto.append(p_res_corr)
                                hr_tag = soup.new_tag('hr', **{'class': 'resposta'})
                                div_acerto.append(hr_tag)
                                p_com_acerto = soup.new_tag('p')
                                p_com_acerto['class'] = '_1-Corpo-Comentario'
                                if com_html.get_text(strip=True):
                                    p_com_acerto.append(BeautifulSoup(str(com_html), 'html.parser'))

                                div_acerto.append(p_com_acerto)

                                # 3. Check Div
                                div_confira = soup.new_tag('div')
                                div_confira['class'] = 'questaoConfira'
                                div_confira['id'] = idD
                                if is_multipla:
                                    p_res_conf = soup.new_tag('p')
                                    p_res_conf['class'] = '_1-Corpo-Resposta'
                                    p_res_conf.append('A alternativa correta é a "')
                                    p_res_conf.append(BeautifulSoup(str(res_html), 'html.parser'))
                                    p_res_conf.append('".')
                                    div_confira.append(p_res_conf)
                                    hr_tag = soup.new_tag('hr', **{'class': 'resposta'})
                                    div_confira.append(hr_tag)
                                    p_com_conf = soup.new_tag('p')
                                    p_com_conf['class'] = '_1-Corpo-Comentario'
                                    if com_html.get_text(strip=True):
                                        p_com_conf.append(BeautifulSoup(str(com_html), 'html.parser'))

                                    div_confira.append(p_com_conf)
                                else:
                                    if dados['resposta']:
                                        p_diss = soup.new_tag('p')
                                        p_diss['class'] = '_1-Corpo-Comentario'
                                        p_diss.append(BeautifulSoup(str(res_html), 'html.parser'))
                                        div_confira.append(p_diss)
                                    if dados['comentario']:
                                        p_diss_c = soup.new_tag('p')
                                        p_diss_c['class'] = '_1-Corpo-Comentario'
                                        if com_html.get_text(strip=True):
                                            p_diss_c.append(BeautifulSoup(str(com_html), 'html.parser'))

                                        div_confira.append(p_diss_c)

                                # Insertion
                                current.insert_before(div_btn)
                                current.insert_before(div_erro)
                                current.insert_before(div_acerto)
                                current.insert_before(div_confira)
                                
                                to_delete = current
                                current = current.find_next_sibling()
                                to_delete.decompose()
                                break
                                
                            current = current.find_next_sibling()

            # Inject Script in Head
            if soup.head:
                if not soup.head.find(string=re.compile("showMe")):
                    soup.head.append(BeautifulSoup(JS_BLOCK, 'html.parser'))
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
