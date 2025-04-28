from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from src import handlers
from settings import settings


if __name__ == "__main__":
    application = ApplicationBuilder().token(settings.bot_token).build()

    start_handler = CommandHandler("start", handlers.start)
    application.add_handler(start_handler)
    create_handler = CommandHandler("create", handlers.create_sin)
    application.add_handler(create_handler)
    vote_handler = CommandHandler("vote", handlers.vote)
    application.add_handler(vote_handler)
    top_handler = CommandHandler("top", handlers.top_sins)
    application.add_handler(top_handler)
    my_sins_handler = CommandHandler("my", handlers.my_sins)
    application.add_handler(my_sins_handler)

    text_handler = MessageHandler(
        filters.TEXT & (~filters.COMMAND), handlers.text_msg
    )
    application.add_handler(text_handler)
    application.add_handler(CallbackQueryHandler(handlers.button_callback))

    print("Start")
    application.run_polling()

# create - Написать грех
# vote - Оценить чужие грехи
# top - Топ грехов
# my - Мои грехи
