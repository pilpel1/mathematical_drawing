import os
import io
import tempfile
from pathlib import Path
import matplotlib.pyplot as plt
from utils.code_executor import SafeCodeExecutor

class RendererService:
    def __init__(self):
        self.executor = SafeCodeExecutor()
        # יצירת תיקיית temp בתוך הפרויקט
        self.temp_dir = Path(__file__).parent.parent / "tempmedia"
        self.temp_dir.mkdir(exist_ok=True)

    def create_image(self, code: str) -> io.BytesIO:
        """
        מקבל קוד matplotlib ומחזיר את התמונה כ-BytesIO
        """
        # ניקוי כל הגרפים הקודמים
        plt.close('all')
        
        # יצירת שם קובץ זמני
        temp_file = self.temp_dir / f"{abs(hash(code))}.png"
        
        try:
            # עדכון הקוד כך שישמור את הקובץ במיקום הנכון
            code_lines = code.split('\n')
            modified_code = []
            for line in code_lines:
                if 'savefig' in line:
                    modified_code.append(f"plt.savefig(r'{temp_file}')")
                else:
                    modified_code.append(line)
            
            # הרצת הקוד המעודכן
            self.executor.execute_code('\n'.join(modified_code))
            
            # וידוא שהקובץ נוצר
            if not temp_file.exists():
                raise RuntimeError("הקובץ לא נוצר כראוי")
            
            # המרת התמונה ל-BytesIO
            img_data = io.BytesIO()
            with open(temp_file, 'rb') as f:
                img_data.write(f.read())
            img_data.seek(0)
            
            return img_data
            
        finally:
            # ניקוי
            self.cleanup(temp_file)

    def cleanup(self, temp_file: Path = None):
        """
        ניקוי קבצים זמניים
        """
        try:
            if temp_file and temp_file.exists():
                temp_file.unlink()
            plt.close('all')
        except Exception as e:
            print(f"שגיאה בניקוי: {e}")

if __name__ == "__main__":
    # דוגמה לשימוש
    code = """
    import matplotlib.pyplot as plt
    import numpy as np
    
    plt.figure(figsize=(8, 8))
    circle = plt.Circle((0, 0), 5, fill=False)
    plt.gca().add_patch(circle)
    plt.axis('equal')
    plt.grid(True)
    plt.savefig('test.png')
    plt.close()
    """
    
    renderer = RendererService()
    img_data = renderer.create_image(code)
    print("Image created successfully!") 