# רשימת מודולים מותרים
ALLOWED_MODULES = {
    'matplotlib',
    'numpy',
    'math',
    'bidi',
    'matplotlib.patches',
    'matplotlib.path',
    'bidi.algorithm'
}

# רשימת מילים אסורות
FORBIDDEN_WORDS = {
    'exec',
    'eval',
    'import os',
    'subprocess',
    'system'
}

# מיפוי מודולים לייבוא גלובלי
GLOBAL_IMPORTS = {
    'matplotlib': '__import__("matplotlib")',
    'plt': '__import__("matplotlib.pyplot").pyplot',
    'numpy': '__import__("numpy")',
    'np': '__import__("numpy")',
    'math': '__import__("math")',
    'get_display': '__import__("bidi.algorithm").get_display',
    'Path': '__import__("matplotlib.path").Path'
} 