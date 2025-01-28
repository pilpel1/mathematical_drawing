import os
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.error import NetworkError, TimedOut

import sys
sys.path.append(str(Path(__file__).parent.parent))

from services.gemini_service import GeminiService
from services.renderer_service import RendererService

# ביטול לוגים של HTTPX
logging.getLogger("httpx").setLevel(logging.WARNING)

# טעינת משתני הסביבה מהתיקייה הראשית של הפרויקט
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# הגדרת לוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MathDrawingBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN')
        if not self.token:
            raise ValueError("לא נמצא טוקן לבוט טלגרם!")
        
        # יצירת השירותים
        self.gemini_service = GeminiService()
        self.renderer_service = RendererService()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """טיפול בפקודת /start"""
        welcome_message = (
            "ברוכים הבאים לבוט השרטוט המתמטי! 🎨\n\n"
            "אני יכול לייצר שרטוטים מתמטיים מתיאור מילולי.\n"
            "פשוט שלחו לי תיאור של השרטוט שאתם רוצים, ואני אייצר אותו עבורכם.\n\n"
            "לדוגמה: 'צייר מעגל במרכז עם רדיוס 5 ובתוכו משולש שווה צלעות'\n\n"
            "לעזרה נוספת, השתמשו בפקודה /help"
        )
        await update.message.reply_text(welcome_message)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """טיפול בפקודת /help"""
        help_message = (
            "הנה כמה דוגמאות לתיאורים שאני מבין:\n\n"
            "1. 'צייר פרבולה y=x^2'\n"
            "2. 'שרטט מעגל ברדיוס 3 עם משיק בנקודה (3,0)'\n"
            "3. 'צייר גרף של פונקציית sin(x) בתחום [-2π,2π]'\n\n"
            "💡 טיפ: עבור צורות גיאומטריות (כמו מעגלים ומשולשים) אני משתמש ברקע נקי.\n"
            "עבור פונקציות וגיאומטריה אנליטית אני מוסיף מערכת צירים.\n"
            "אם תרצו סגנון תצוגה שונה, פשוט ציינו זאת בתיאור!\n\n"
            "פשוט שלחו לי תיאור בעברית של מה שאתם רוצים לצייר!"
        )
        await update.message.reply_text(help_message)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """טיפול בהודעות טקסט רגילות"""
        try:
            # שליחת הודעת המתנה
            processing_message = await update.message.reply_text(
                "מעבד את הבקשה שלך... 🎨"
            )
            
            # יצירת הקוד באמצעות Gemini
            code = self.gemini_service.generate_code(update.message.text)
            
            # וידוא שהקוד בטוח
            if not self.gemini_service.validate_code(code):
                await processing_message.edit_text("מצטער, הקוד שנוצר אינו בטוח להרצה 😕")
                return
            
            # יצירת התמונה
            img_data = self.renderer_service.create_image(code)
            
            # שליחת התמונה
            await update.message.reply_photo(
                photo=img_data,
                caption="הנה השרטוט שביקשת! 🎨"
            )
            
            # מחיקת הודעת ההמתנה
            await processing_message.delete()
            
        except Exception as e:
            error_message = f"מצטער, נתקלתי בשגיאה: {str(e)} 😕"
            if 'processing_message' in locals():
                await processing_message.edit_text(error_message)
            else:
                await update.message.reply_text(error_message)

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """טיפול בשגיאות"""
        try:
            raise context.error
        except (NetworkError, TimedOut):
            # במקרה של שגיאת רשת, ננסה שוב אחרי 5 שניות
            logger.warning("שגיאת רשת, מנסה שוב בעוד 5 שניות...")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"שגיאה לא צפויה: {str(e)}")

    def run(self):
        """הפעלת הבוט"""
        # יצירת האפליקציה
        application = Application.builder().token(self.token).build()

        # הוספת הטיפול בפקודות
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help))
        
        # הוספת הטיפול בהודעות טקסט
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # הוספת טיפול בשגיאות
        application.add_error_handler(self.error_handler)

        # הפעלת הבוט
        logger.info("הבוט מתחיל לרוץ...")
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    bot = MathDrawingBot()
    bot.run() 