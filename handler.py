from telegram import Bot, Update
from telegram.ext import InlineQueryHandler
from telegram.ext.dispatcher import run_async

@run_async
def wxmpbot_inline_query_callback(bot: Bot, update: Update):
    pass

wxmpbotInlineQueryHandler = InlineQueryHandler(wxmpbot_inline_query_callback)
