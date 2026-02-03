import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # AI Configuration
    AI_API_URL = os.getenv("AI_API_URL", "http://localhost:1234/v1/chat/completions")
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "local-model")
    AI_PROVIDER = os.getenv("AI_PROVIDER", "lm-studio")
    
    # Cleaning Patterns
    # Note: Split into list to avoid variable-length lookbehind errors in Python re module.
    # Pattern logic: Remove id="_id..." attributes unless they are preceded by specific classes.
    
    REGEX_REMOVE_PATTERNS = [
        # 1. Remove IDs starting with _id, EXCEPT provided classes.
        # Uses chained fixed-width lookbehinds.
        # Matches: id="_id..." including the closing quote.
        r'(?<!class="_0-Titulo-Artigo" )(?<!class="_1-Titulo-1" )id="_id[^"]*"',
        
        # 2. Other cleanups
        r'_idGenObjectStyle-Disabled',
        r'xml:lang=".*?"',
        r'lang=".*?"',
        r'\sclass="negrito"',
        r'\sclass="italico"',
        r'\sclass="sobrescrito"',
        r'\sclass="subscrito"'
    ]

    # H1 cleaning pattern
    REGEX_H1_UL_FIX = {
        "pattern": r'(<h2 class="_1-Titulo-1".*?</h2>)</li>\s*</ul>\s*</li>\s*</ul>\1',
    }
