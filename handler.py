import re
import html
import logging
import traceback
from telegram import Bot, Update
from telegram import InlineQuery, InlineQueryResult, InlineQueryResultArticle, InputTextMessageContent
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, InlineQueryHandler
from telegram.ext.dispatcher import run_async
from grpc import RpcError
from proto.wxfetcher_pb2 import FetchURLRequest, FetchURLResponse, ArticleMeta, FetchURLError
from proto.wxfetcher_pb2_grpc import WxFetcherStub
from storage import get
from typing import Tuple, List

_REGEX_URL = re.compile(r"(?:http|https)://[\w-]+(?:\.[\w-]+)+(?:[\w.,;@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?", re.ASCII)

logger = logging.getLogger("Handler")

@run_async
def wxmpbot_start_command_callback(bot: Bot, update: Update):
    msg = update.message
    args = msg.text.split()
    if "bielaiwuyang" in args:
        msg.reply_text("嗨，别来无恙啊！")
    if "chui" in args:
        bot.send_message(
            get("tg", "admin"), "要锤 @mutong 吗？",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton("好喔！", callback_data="chui")]]
            )
        )

wxmpbotStartCommandHandler = CommandHandler("start", wxmpbot_start_command_callback)

@run_async
def wxmpbot_inline_query_callback(bot: Bot, update: Update):
    query = update.inline_query  # type: InlineQuery
    try:
        if _REGEX_URL.fullmatch(query.query):
            answer, notification, param, details = _full_match_mode(query.query)
        else:
            answer, notification, param, details = [], "嗨，别来无恙啊！", "bielaiwuyang", None
        query.answer(results=answer, switch_pm_text=notification, switch_pm_parameter=param, cache_time=10)
        if details is not None:
            bot.send_message(
                get("tg", "admin"),
                "Query:\n<pre>{}</pre>\n\nMessage:\n<pre>{}</pre>".format(
                    html.escape(query.query), html.escape(details)
                ), parse_mode="HTML"
            )
    except Exception:
        logger.exception("Unexpected error in inline_query_callback.")
        query.answer(results=[], switch_pm_text="出错了，快去锤 @mutong", switch_pm_parameter="error_unexpected chui", cache_time=10)
        bot.send_message(
            get("tg", "admin"),
            "Query:\n<pre>{}</pre>\n\nTraceback:\n<pre>{}</pre>".format(
                html.escape(query.query), html.escape(traceback.format_exc())
            ), parse_mode="HTML"
        )

wxmpbotInlineQueryHandler = InlineQueryHandler(wxmpbot_inline_query_callback)


def _is_url_supported(url: str) -> bool:
    return url.startswith("http://mp.weixin.qq.com/") or url.startswith("https://mp.weixin.qq.com/")


def _full_match_mode(text: str) -> Tuple[List[InlineQueryResult], str, str, str]:
    fetcher = get("rpc", "stub")  # type: WxFetcherStub
    url = html.unescape(text)
    if not _is_url_supported(url):
        return [], "不支持的链接", "error_unsupported", None
    try:
        fetch_req = FetchURLRequest(url=url)
        fetch_resp = fetcher.FetchURL(fetch_req)  # type: FetchURLResponse
        if fetch_resp.error == FetchURLError.Value("OK"):
            prefix, key, meta = get("prefix"), fetch_resp.key, fetch_resp.meta  # type: str, str, ArticleMeta
            link = "{}/{}".format(prefix, key)
            return \
                [
                    InlineQueryResultArticle(
                        id="{}|0".format(key),
                        title="带预览的链接",
                        description=link,
                        thumb_url=meta.image,
                        input_message_content=InputTextMessageContent(link)),
                    InlineQueryResultArticle(
                        id="{}|1".format(key),
                        title="文章标题",
                        description=meta.title,
                        thumb_url=meta.image,
                        input_message_content=InputTextMessageContent("<a href=\"{}\">{}</a>".format(
                            link, html.escape(meta.title)
                        ), parse_mode="HTML", disable_web_page_preview=True)),
                    InlineQueryResultArticle(
                        id="{}|2".format(key),
                        title="标题与摘要",
                        description=meta.brief,
                        thumb_url=meta.image,
                        input_message_content=InputTextMessageContent("<a href=\"{}\">{}</a>\n<pre>{}</pre>".format(
                            link, html.escape(meta.title), html.escape(meta.brief)
                        ), parse_mode="HTML", disable_web_page_preview=True))
                ], "嗨，别来无恙啊！", "bielaiwuyang", None
        elif fetch_resp.error == FetchURLError.Value("UNSUPPORTED"):
            return [], "不支持的链接", "error_unsupported", None
        elif fetch_resp.error == FetchURLError.Value("NETWORK"):
            return [], "网络错误，快去锤 @mutong", "error_network chui", fetch_resp.msg
        elif fetch_resp.error == FetchURLError.Value("PARSE"):
            return [], fetch_resp.msg, "error_parse", None
        elif fetch_resp.error == FetchURLError.Value("INTERNAL"):
            return [], "出错了，快去锤 @mutong", "error_internal chui", fetch_resp.msg
    except RpcError as e:
        return [], "服务器炸了，快锤 @mutong", "error_rpc", str(e)
