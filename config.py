class Config:
    # LM Studio Configuration
    LM_STUDIO_URL = "http://192.168.28.70:1234/v1/chat/completions"
    LM_STUDIO_MODEL = "local-model" 
    
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
