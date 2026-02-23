# EPUB Automation - InteratividadePRO

Esta aplicação automatiza o processamento e aprimoramento de arquivos EPUB para o ecossistema InteratividadePRO. Ela realiza limpezas estruturais, injeção de fontes, adição de interatividade em atividades e identificação automática de tópicos via IA.

## Funcionalidades Principais

- **Processamento em Lote**: Processa automaticamente todos os arquivos `.epub` na pasta `input/`.
- **Limpeza estrutural**: Remove resíduos de exportação do InDesign e normaliza atributos HTML.
- **Interatividade**: Transforma gabaritos estáticos em atividades interativas com feedback instantâneo (via jQuery).
- **IA Generativa**: Identifica e marca automaticamente tabelas e tópicos usando modelos de linguagem.
- **Injeção de Fontes**: Garante que todas as fontes necessárias estejam embarcadas no arquivo.
- **Auditoria de Integridade**: Verifica se o número de elementos (parágrafos, imagens, tabelas) permanece consistente após o processamento.
- **Scanner de QR Code**: Identifica links embutidos em imagens de QR Code.

## Módulos

- `auditor.py`: Valida a integridade dos dados comparando contagens de elementos antes e depois.
- `cleaner.py`: Limpa o HTML usando regex e remove estruturas desnecessárias.
- `font_injector.py`: Copia fontes de `assets/fonts` para o EPUB e atualiza o manifesto.
- `interactivity.py`: Injeta lógica JavaScript e jQuery para criar atividades interativas.
- `ncx_generator.py`: Gera/atualiza o arquivo de navegação NCX.
- `qr_scanner.py`: Localiza e extrai informações de QR Codes nas imagens do livro.
- `structure.py`: Ajusta containers de imagem para conformidade visual.
- `topic_identifier.py`: Integração com API de IA para rotulagem inteligente de conteúdo.
- `url_linker.py`: Converte URLs de texto puro em links clicáveis (`<a>`).

## Instalação

### Requisitos
- Python 3.8+
- Git

### Passo a Passo

1. **Clonar o repositório**:
   ```bash
   git clone <url-do-repositorio>
   cd epub_automation
   ```

2. **Criar e ativar o ambiente virtual**:
   ```bash
   python -m venv epub_automation
   # No Windows:
   .\epub_automation\Scripts\activate
   # No Linux/Mac:
   source epub_automation/bin/activate
   ```

3. **Instalar dependências**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuração**:
   Crie um arquivo `.env` na raiz do projeto (use o exemplo se disponível) com as credenciais da API de IA.

## Como Usar

1. Coloque seus arquivos `.epub` na pasta `input/`.
2. Execute o script principal:
   ```bash
   python main.py
   ```
3. O resultado aparecerá na pasta `output/` com o sufixo `_v2`.

### Flags Adicionais

- `--nolinks`: Desativa a conversão automática de URLs em links.
- `--input <caminho>`: Especifica um arquivo ou diretório de entrada diferente.
- `--output <caminho>`: Especifica um diretório de saída diferente.

---
Desenvolvido para otimização de fluxo editorial digital.
