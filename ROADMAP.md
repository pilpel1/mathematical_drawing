# Mathematical Drawing Bot - מפרט טכני ותכנון

## תיאור הפרויקט
בוט טלגרם שמקבל תיאור מילולי של שרטוט מתמטי, מייצר אותו באמצעות Gemini AI ושולח חזרה למשתמש.

## ארכיטקטורה
```
mathematical_drawing/
├── requirements.txt
├── .env
├── .gitignore
├── README.md
├── config.py
├── bot/
│   ├── __init__.py
│   ├── telegram_bot.py
│   └── message_handler.py
├── services/
│   ├── __init__.py
│   ├── gemini_service.py
│   └── renderer_service.py
└── utils/
    ├── __init__.py
    └── code_executor.py
```

## דרישות טכניות
- Python 3.10+
- Virtual Environment
- תלויות חיצוניות:
  - python-telegram-bot==20.7
  - google-generativeai==0.3.1
  - matplotlib==3.8.2
  - python-dotenv==1.0.0

## מודולים עיקריים

### 1. Bot Module (`bot/telegram_bot.py`)
- מחלקה: `MathDrawingBot`
- פונקציות:
  - `start_handler`: טיפול בפקודת /start
  - `help_handler`: טיפול בפקודת /help
  - `process_description`: טיפול בתיאור מילולי
  - `send_image`: שליחת התמונה שנוצרה

### 2. Gemini Service (`services/gemini_service.py`)
- מחלקה: `GeminiService`
- פונקציות:
  - `generate_code`: יצירת קוד matplotlib מתיאור
  - `validate_code`: וידוא שהקוד בטוח ומתאים
  - פרומפט בסיסי לדוגמה:
    ```
    "Create matplotlib code for the following mathematical drawing: {description}. 
    Use only matplotlib and math libraries. Return only the code without explanations."
    ```

### 3. Renderer Service (`services/renderer_service.py`)
- מחלקה: `RendererService`
- פונקציות:
  - `execute_code`: הרצת הקוד בסביבה מבודדת
  - `create_image`: יצירת תמונה מהפלט
  - `cleanup`: ניקוי משאבים

### 4. Code Executor (`utils/code_executor.py`)
- מחלקה: `SafeCodeExecutor`
- הגבלות אבטחה:
  - רשימת import מותרים
  - הגבלת זמן ריצה
  - הגבלת שימוש בזיכרון
  - בידוד מערכת הקבצים

## שלבי פיתוח

### שלב 1: תשתית (2-3 ימים)
- [x] הקמת סביבת פיתוח
- [ ] הגדרת תלויות
- [ ] הקמת בוט טלגרם בסיסי

### שלב 2: אינטגרציה עם Gemini (3-4 ימים)
- [ ] מימוש GeminiService
- [ ] פיתוח מנגנון וולידציה
- [ ] טיפול בשגיאות

### שלב 3: מנוע רינדור (2-3 ימים)
- [ ] פיתוח SafeCodeExecutor
- [ ] מימוש RendererService
- [ ] טיפול בקצה מקרים

### שלב 4: אינטגרציה ובדיקות (2-3 ימים)
- [ ] חיבור כל המודולים
- [ ] בדיקות מקיפות
- [ ] טיפול בשגיאות קצה

## שיקולי אבטחה
1. וולידציה כפולה של הקוד באמצעות Gemini
2. הרצה בסביבה מבודדת
3. הגבלת ספריות מותרות
4. טיפול בשגיאות זמן ריצה
5. ניקוי משאבים אחרי כל הרצה

## דוגמאות לשימוש
```python
# דוגמה לתיאור מילולי:
"צייר מעגל במרכז עם רדיוס 5 ובתוכו משולש שווה צלעות"

# קוד שאמור להיווצר:
import matplotlib.pyplot as plt
import math

fig, ax = plt.subplots()
circle = plt.Circle((0, 0), 5, fill=False)
ax.add_patch(circle)

# יצירת משולש שווה צלעות
r = 5 * 0.8  # 80% מרדיוס המעגל
angles = [0, 120, 240]
points = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) 
          for a in angles]

plt.plot([p[0] for p in points + [points[0]]], 
         [p[1] for p in points + [points[0]]], 'b-')

ax.set_aspect('equal')
plt.axis('off')
```

## הערות נוספות
1. שימוש ב-BytesIO לשליחת תמונות
2. לוגים מפורטים לדיבוג
3. מערכת שגיאות ברורה למשתמש
4. אפשרות להרחבה עתידית 