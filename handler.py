import re
import html
import logging
import traceback
from telegram import Bot, Update
from telegram import Message, InlineQuery, CallbackQuery
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, InlineQueryHandler, CallbackQueryHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async
from grpc import RpcError
from proto.wxfetcher_pb2 import FetchURLRequest, FetchURLResponse, ArticleMeta, FetchURLError
from proto.wxfetcher_pb2_grpc import WxFetcherStub
from storage import get
from typing import Tuple, List, Optional

_REGEX_URL = re.compile(r"(?:http|https)://[\w-]+(?:\.[\w-]+)+(?:[\w.,;@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?", re.ASCII)

logger = logging.getLogger("Handler")


@run_async
def wxmpbot_start_command_callback(bot: Bot, update: Update):
    msg = update.message  # type: Message
    args = msg.text.split()
    if "bielaiwuyang" in args:
        msg.reply_text("嗨，别来无恙啊！")
    if "chui" in args:
        msg.reply_text(
            "要锤 @mutong 吗？",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton("好喔！", callback_data="chui")]]
            )
        )


@run_async
def wxmpbot_callback_query_callback(bot: Bot, update: Update):
    cb = update.callback_query  # type: CallbackQuery
    if cb.data == "chui":
        bot.send_message(
            get("tg", "admin"), "<a href=\"tg://user?id={}\">{}</a> 来锤你了！".format(
                cb.from_user.id, cb.from_user.full_name
            ), parse_mode="HTML"
        )
        cb.message.edit_text("锤到 @mutong 了！")


@run_async
def wxmpbot_text_message_callback(bot: Bot, update: Update):
    msg = update.message  # type: Message
    try:
        if _REGEX_URL.fullmatch(msg.text):
            link, meta, notification, param, detail = _process_url(msg.text)
            answer = link if link is not None else notification
        else:
            answer, detail = "这看起来不是一个链接啦！", None
    except Exception:
        logger.exception("Unexpected error in text_message_callback.")
        answer, detail = "出错了，快去锤 @mutong", traceback.format_exc()
    msg.reply_text(answer)
    if detail is not None:
        bot.send_message(
            get("tg", "admin"),
            "Error in <pre>text_message_callback</pre>\nText:\n<pre>{}</pre>\n\nError:\n<pre>{}</pre>".format(
                html.escape(msg.text), html.escape(detail)
            ), parse_mode="HTML"
        )

@run_async
def wxmpbot_inline_query_callback(bot: Bot, update: Update):
    query = update.inline_query  # type: InlineQuery
    try:
        if _REGEX_URL.fullmatch(query.query):
            link, meta, notification, param, detail = _process_url(query.query)
            answer = [
                InlineQueryResultArticle(
                    id="{}|link".format(link),
                    title="带预览的链接",
                    description=link,
                    thumb_url=meta.image,
                    input_message_content=InputTextMessageContent(link)),
                InlineQueryResultArticle(
                    id="{}|title".format(link),
                    title="文章标题",
                    description=meta.title,
                    thumb_url=meta.image,
                    input_message_content=InputTextMessageContent("<a href=\"{}\">{}</a>".format(
                        link, html.escape(meta.title)
                    ), parse_mode="HTML", disable_web_page_preview=True)),
                InlineQueryResultArticle(
                    id="{}|brief".format(link),
                    title="标题与摘要",
                    description=meta.brief,
                    thumb_url=meta.image,
                    input_message_content=InputTextMessageContent("<a href=\"{}\">{}</a>\n<pre>{}</pre>".format(
                        link, html.escape(meta.title), html.escape(meta.brief)
                    ), parse_mode="HTML", disable_web_page_preview=True))
            ] if link is not None else []
        else:
            answer, notification, param, detail = [], "嗨，别来无恙啊！", "bielaiwuyang", None
    except Exception:
        logger.exception("Unexpected error in inline_query_callback.")
        answer, notification, param, detail = [], "出错了，快去锤 @mutong", "error_unexpected chui", traceback.format_exc()
    # Send bot answer
    query.answer(results=answer, switch_pm_text=notification, switch_pm_parameter=param, cache_time=10)
    if detail is not None:
        bot.send_message(
            get("tg", "admin"),
            "Error in <pre>inline_query_callback</pre>\nQuery:\n<pre>{}</pre>\n\nError:\n<pre>{}</pre>".format(
                html.escape(query.query), html.escape(detail)
            ), parse_mode="HTML"
        )


wxmpbotStartCommandHandler = CommandHandler("start", wxmpbot_start_command_callback)
wxmpbotCallbackQueryHandler = CallbackQueryHandler(wxmpbot_callback_query_callback)
wxmpbotTextMessageHandler = MessageHandler(Filters.text, wxmpbot_text_message_callback)
wxmpbotInlineQueryHandler = InlineQueryHandler(wxmpbot_inline_query_callback)


def _process_url(url: str) -> Tuple[Optional[str], Optional[ArticleMeta], str, str, Optional[str]]:
    """
    Returns:
    - Link (str)
    - Article Meta
    - User Notification (str)
    - Inline Start Param (str)
    - Detailed Error Message
    """
    fetcher = get("rpc", "stub")  # type: WxFetcherStub
    url = html.unescape(url)
    if not _is_url_supported(url):
        return None, None, "不支持的链接", "error_unsupported", None
    try:
        fetch_req = FetchURLRequest(url=url)
        fetch_resp = fetcher.FetchURL(fetch_req)  # type: FetchURLResponse
        if fetch_resp.error == FetchURLError.Value("OK"):
            link = "{}/{}".format(get("prefix"), fetch_resp.key)
            return link, fetch_resp.meta, "嗨，别来无恙啊！", "bielaiwuyang", None
        if fetch_resp.error == FetchURLError.Value("UNSUPPORTED"):
            return None, None, "不支持的链接", "error_unsupported", None
        if fetch_resp.error == FetchURLError.Value("NETWORK"):
            return None, None, "网络错误，快去锤 @mutong", "error_network chui", fetch_resp.msg
        if fetch_resp.error == FetchURLError.Value("PARSE"):
            return None, None, fetch_resp.msg.capitalize(), "error_parse", None
        if fetch_resp.error == FetchURLError.Value("INTERNAL"):
            return None, None, "出错了，快去锤 @mutong", "error_internal chui", fetch_resp.msg
    except RpcError as e:
        return None, None, "服务器炸了，快去锤 @mutong", "error_rpc chui", str(e)


def _is_url_supported(url: str) -> bool:
    return url.startswith("http://mp.weixin.qq.com/") or url.startswith("https://mp.weixin.qq.com/")
