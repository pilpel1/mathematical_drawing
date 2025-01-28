import os
import sys
import ast
import builtins
from pathlib import Path
from dotenv import load_dotenv

# טעינת משתני הסביבה
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class SafeCodeExecutor:
    def __init__(self):
        self.max_execution_time = int(os.getenv('MAX_EXECUTION_TIME', 30))
        self.allowed_modules = {'matplotlib', 'numpy', 'math'}
        
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
                'enumerate': enumerate
            }
        }

    def execute_code(self, code: str) -> None:
        """
        מריץ קוד Python בצורה בטוחה
        """
        # בדיקת תחביר
        try:
            ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"שגיאת תחביר בקוד: {e}")

        # בדיקת ייבוא מודולים
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = node.names[0].name.split('.')[0]
                if module not in self.allowed_modules:
                    raise ValueError(f"מודול לא מורשה: {module}")

        # הרצת הקוד בסביבה בטוחה
        try:
            # ייבוא המודולים בזמן ריצה
            globals_dict = self.safe_builtins.copy()
            globals_dict.update({
                'matplotlib': __import__('matplotlib'),
                'plt': __import__('matplotlib.pyplot').pyplot,
                'numpy': __import__('numpy'),
                'np': __import__('numpy'),
                'math': __import__('math')
            })
            exec(code, globals_dict)
        except Exception as e:
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