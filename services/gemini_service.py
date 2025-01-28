import os
import time
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# טעינת משתני הסביבה
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("לא נמצא מפתח API של Gemini!")
        
        # הגדרת Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')
        
        # הגדרות retry
        self.max_retries = 3
        self.retry_delay = 2  # שניות

    def generate_code(self, description: str) -> str:
        """
        מקבל תיאור מילולי ומייצר קוד matplotlib מתאים
        """
        prompt = f"""Create matplotlib code for the following mathematical drawing: {description}
        Important guidelines:
        1. Use only matplotlib and math libraries
        2. Return ONLY the Python code without any explanations
        3. Make sure the code is complete and can run independently
        4. For Hebrew text in labels or titles:
           - Use plt.rcParams['font.family'] = 'Arial' at the start
           - Add plt.rcParams['font.size'] = 12
           - For any Hebrew text, write it from left to right but add [::-1] at the end
             Example: title = "שרטוט מתמטי"[::-1]
        5. When setting axis labels and ticks:
           - First use ax.set_xticks() to set tick positions
           - Then use ax.set_xticklabels() to set labels
           - Do the same for y-axis
        6. Use plt.savefig() instead of plt.show()
        7. Clean up the plot after saving using plt.close()
        8. Make sure to set figure size to (10, 10)
        9. For the plot style:
           - For geometric shapes (circles, triangles, polygons etc.) use a clean white background without grid or axes unless specifically requested
           - For functions and analytical geometry (graphs, curves, etc.) include a proper coordinate system with grid
           - Always use plt.axis('equal') for geometric shapes to maintain proportions
           - Use clear, contrasting colors for better visibility
        """

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.model.generate_content(prompt)
                return self._extract_code(response.text)
            except Exception as e:
                last_error = e
                if "500" in str(e):
                    # אם זו שגיאת שרת, נחכה ונסה שוב
                    if attempt < self.max_retries - 1:  # אם זה לא הניסיון האחרון
                        time.sleep(self.retry_delay * (attempt + 1))  # המתנה גדלה עם כל ניסיון
                        continue
                # אם זו לא שגיאת 500 או שזה הניסיון האחרון, נזרוק את השגיאה
                raise RuntimeError(f"נכשל ליצור קוד אחרי {self.max_retries} ניסיונות. שגיאה אחרונה: {str(last_error)}")

    def validate_code(self, code: str) -> bool:
        """
        בודק שהקוד בטוח ומתאים להרצה
        """
        # רשימת מילים אסורות
        forbidden = ['exec', 'eval', 'import os', 'subprocess', 'system']
        
        # רשימת ספריות מותרות
        allowed_imports = ['matplotlib', 'numpy', 'math']
        
        code_lower = code.lower()
        
        # בדיקת מילים אסורות
        if any(word in code_lower for word in forbidden):
            return False
            
        # בדיקת ייבוא ספריות
        import_lines = [line.strip() for line in code.split('\n') 
                       if line.strip().startswith('import') or 'from' in line]
        
        for line in import_lines:
            if not any(lib in line for lib in allowed_imports):
                return False
                
        return True

    def _extract_code(self, response: str) -> str:
        """
        מחלץ את הקוד מתוך תשובת Gemini
        """
        # אם התשובה מכילה בלוק קוד
        if '```python' in response:
            code = response.split('```python')[1].split('```')[0]
        elif '```' in response:
            code = response.split('```')[1].split('```')[0]
        else:
            code = response
            
        return code.strip()

if __name__ == "__main__":
    # דוגמה לשימוש
    service = GeminiService()
    description = "צייר מעגל במרכז עם רדיוס 5 ובתוכו משולש שווה צלעות"
    code = service.generate_code(description)
    print("Generated Code:")
    print(code) 