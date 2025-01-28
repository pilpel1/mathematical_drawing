import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# טעינת משתני הסביבה
load_dotenv()

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
            "פשוט שלחו לי תיאור בעברית של מה שאתם רוצים לצייר!"
        )
        await update.message.reply_text(help_message)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """טיפול בהודעות טקסט רגילות"""
        # בשלב זה נחזיר רק הודעת אישור
        await update.message.reply_text(
            f"קיבלתי את הבקשה שלך: '{update.message.text}'\n"
            "בקרוב אוכל לייצר עבורך את השרטוט המבוקש!"
        )

    def run(self):
        """הפעלת הבוט"""
        # יצירת האפליקציה
        application = Application.builder().token(self.token).build()

        # הוספת הטיפול בפקודות
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help))
        
        # הוספת הטיפול בהודעות טקסט
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # הפעלת הבוט
        logger.info("הבוט מתחיל לרוץ...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    bot = MathDrawingBot()
    bot.run() 