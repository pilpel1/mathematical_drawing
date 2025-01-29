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
            "💡 טיפ: ככל שהבקשה פשוטה יותר, כך הסיכוי להצלחה גבוה יותר.\n"
            "לדוגמה: 'צייר מעגל במרכז עם רדיוס 5 ובתוכו משולש שווה צלעות'\n\n"
            "⚠️ שימו לב: יתכנו אי-דיוקים או אי-הבנות, במיוחד בבקשות מורכבות.\n\n"
            "לעזרה נוספת ודוגמאות, השתמשו בפקודה /help"
        )
        await update.message.reply_text(welcome_message)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """טיפול בפקודת /help"""
        help_message = (
            "הנה כמה דוגמאות לתיאורים שאני מבין היטב:\n\n"
            "✅ בקשות פשוטות (סיכויי הצלחה גבוהים):\n"
            "1. 'צייר מעגל ברדיוס 3'\n"
            "2. 'שרטט פרבולה y=x^2'\n"
            "3. 'צייר גרף של sin(x) בתחום [-2π,2π]'\n\n"
            "⚠️ בקשות מורכבות (יתכנו אי-דיוקים):\n"
            "1. 'צייר מעגל עם משיק ומיתר שווים'\n"
            "2. 'שרטט משולש עם כל הגבהים והתיכונים'\n\n"
            "💡 טיפים להצלחה:\n"
            "• נסחו את הבקשה בצורה ברורה ופשוטה\n"
            "• הימנעו מבקשות עם יותר מדי פרטים בבת אחת\n"
            "• אם התוצאה לא מדויקת, נסו לנסח את הבקשה אחרת\n\n"
            "🎨 סגנון התצוגה:\n"
            "• צורות גיאומטריות: רקע נקי\n"
            "• פונקציות וגרפים: כולל מערכת צירים\n"
            "אם תרצו סגנון תצוגה שונה, פשוט ציינו זאת בתיאור!"
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
            try:
                code = self.gemini_service.generate_code(update.message.text)
            except RuntimeError as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    logger.warning("Gemini rate limit reached")
                    await processing_message.edit_text(
                        "מצטער, הגענו למגבלת הבקשות של המערכת. אנא נסה שוב בעוד כמה דקות 🕒"
                    )
                    return
                raise  # Re-raise if it's not a rate limit error
            
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
            # רישום השגיאה המלאה בלוגים
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            
            # שליחת הודעה כללית למשתמש
            error_message = "מצטער, נתקלתי בשגיאה בעיבוד הבקשה. אנא נסה שוב או נסח את הבקשה בצורה שונה 😕"
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
            logger.warning("Network error, retrying in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")

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
        logger.info("Bot is starting...")
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    bot = MathDrawingBot()
    bot.run() 