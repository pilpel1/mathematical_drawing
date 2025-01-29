import os
import sys
import ast
import json
import builtins
import logging
import traceback
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from .config import ALLOWED_MODULES, FORBIDDEN_WORDS, GLOBAL_IMPORTS

# הגדרת לוגר
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

# הגדרת לוגר לקובץ JSON
class JSONFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
        self.logs = []

    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line_number': record.lineno,
            'process': record.process,
            'thread': record.thread,
            'full_path': record.pathname
        }
        
        # הוספת מידע על חריגות
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            log_entry['exception'] = {
                'type': str(exc_type.__name__),
                'message': str(exc_value),
                'traceback': traceback.format_exception(exc_type, exc_value, exc_tb),
                'stack_info': record.stack_info
            }
            
        # הוספת מידע נוסף אם קיים
        if hasattr(record, 'code'):
            log_entry['code'] = record.code
        
        return json.dumps(log_entry, ensure_ascii=False)

class JSONHandler(logging.FileHandler):
    def __init__(self, filename, mode='a', encoding='utf-8'):
        super().__init__(filename, mode, encoding=encoding)
        self.logs = []
        self.formatter = JSONFormatter()

    def emit(self, record):
        try:
            msg = self.formatter.format(record)
            log_entry = json.loads(msg)
            self.logs.append(log_entry)
            
            # כתיבת כל הלוגים כמערך JSON אחד
            with open(self.baseFilename, 'w', encoding=self.encoding) as f:
                json.dump(self.logs, f, ensure_ascii=False, indent=2)
                
        except Exception:
            self.handleError(record)

class ConsoleFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno >= logging.WARNING:
            return f"{record.levelname}: {record.getMessage()}"
        return ""

# הגדרת הלוגר
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False  # מניעת לוגים כפולים

# הגדרת handler לקובץ JSON
json_handler = JSONHandler(log_dir / 'code_execution.json')
json_handler.setLevel(logging.DEBUG)
logger.addHandler(json_handler)

# הגדרת handler לקונסול - רק אזהרות ושגיאות
console_handler = logging.StreamHandler()
console_handler.setFormatter(ConsoleFormatter())
console_handler.setLevel(logging.WARNING)
logger.addHandler(console_handler)

# טעינת משתני הסביבה
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class SafeCodeExecutor:
    def __init__(self):
        self.max_execution_time = int(os.getenv('MAX_EXECUTION_TIME', 30))
        self.allowed_modules = ALLOWED_MODULES
        
        # יצירת סביבת הרצה בטוחה
        self.safe_builtins = {
            '__builtins__': {
                '__import__': __import__,
                'print': print,
                'len': len,
                'range': range,
                'int': int,
                'float': float,
                'str': str,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'bool': bool,
                'True': True,
                'False': False,
                'None': None,
                'min': min,
                'max': max,
                'abs': abs,
                'sum': sum,
                'round': round,
                'pow': pow,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'sorted': sorted,
                'reversed': reversed
            }
        }

    def validate_code(self, code: str) -> bool:
        """
        בודק שהקוד בטוח ומתאים להרצה
        """
        logger.info("Starting code validation")
        logger.debug(f"Code to validate:\n{code}")
        
        code_lower = code.lower()
        
        # בדיקת מילים אסורות
        for word in FORBIDDEN_WORDS:
            if word in code_lower:
                logger.warning(f"Validation failed: Found forbidden word: {word}")
                return False
            
        # בדיקת ייבוא ספריות
        import_lines = [
            line.strip() 
            for line in code.split('\n') 
            if line.strip() and (
                line.strip().startswith('import ') or  # חייב רווח אחרי import
                (line.strip().startswith('from ') and ' import ' in line.strip())  # חייב רווח אחרי from ו-import
            )
        ]
        
        logger.info("Found import lines:")
        for line in import_lines:
            logger.info(f"  {line}")
            if not any(lib in line for lib in self.allowed_modules):
                logger.warning(f"Validation failed: Unauthorized import: {line}")
                return False
        
        logger.info("Code validation passed")
        return True

    def execute_code(self, code: str) -> None:
        """
        מריץ קוד Python בצורה בטוחה
        """
        logger.info("Starting code execution")
        logger.debug(f"Code to execute:\n{code}")
        
        # בדיקת תחביר
        try:
            ast.parse(code)
        except SyntaxError as e:
            logger.error(f"Syntax error in code: {e}")
            raise ValueError(f"שגיאת תחביר בקוד: {e}")

        # בדיקת ייבוא מודולים
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.ImportFrom):
                    module = node.module.split('.')[0]  # קח את המודול הראשי
                else:
                    module = node.names[0].name.split('.')[0]
                logger.info(f"Checking module: {module}")
                if module not in self.allowed_modules:
                    logger.warning(f"Unauthorized module detected: {module}")
                    raise ValueError(f"מודול לא מורשה: {module}")

        # הרצת הקוד בסביבה בטוחה
        try:
            # ייבוא המודולים בזמן ריצה
            globals_dict = self.safe_builtins.copy()
            
            # קודם נייבא את כל המודולים הבסיסיים
            for name, import_str in GLOBAL_IMPORTS.items():
                if not import_str.startswith('patches.'):
                    try:
                        if name == 'get_display':
                            # ייבוא מיוחד ל-get_display
                            from bidi.algorithm import get_display as bidi_get_display
                            globals_dict[name] = bidi_get_display
                        else:
                            globals_dict[name] = eval(import_str)
                    except Exception as e:
                        logger.error(f"Error importing {name}: {str(e)}")
                        raise
            
            # אחר כך נייבא את כל האובייקטים מ-patches
            from matplotlib.patches import PathPatch, Polygon, Circle, Rectangle, Arc
            globals_dict.update({
                'PathPatch': PathPatch,
                'Polygon': Polygon,
                'Circle': Circle,
                'Rectangle': Rectangle,
                'Arc': Arc
            })
            
            exec(code, globals_dict)
            logger.info("Code executed successfully")
        except Exception as e:
            logger.error(f"Error during code execution: {str(e)}", exc_info=True)
            raise RuntimeError(f"שגיאה בהרצת הקוד: {str(e)}")

if __name__ == "__main__":
    # דוגמה לשימוש
    code = """
    import matplotlib.pyplot as plt
    import numpy as np
    
    x = np.linspace(-5, 5, 100)
    y = x**2
    
    plt.plot(x, y)
    plt.savefig('test.png')
    plt.close()
    """
    
    executor = SafeCodeExecutor()
    executor.execute_code(code)
    print("Code executed successfully!") 