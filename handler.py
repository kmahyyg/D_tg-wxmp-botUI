import re
from telegram import Bot, Update, InlineQuery
from telegram.ext import InlineQueryHandler
from telegram.ext.dispatcher import run_async
from grpc import RpcError
from proto.wxfetcher_pb2 import FetchURLRequest, FetchURLResponse
from proto.wxfetcher_pb2_grpc import WxFetcherStub
from storage import get, put

_REGEX_URL = re.compile(
    r"(?:http|https)://[\w-]+(?:\.[\w-]+)+(?:[\w.,@?^=%&:;/~+#-]*[\w@?^=%&/~+#-])?",
    re.ASCII,
)


@run_async
def wxmpbot_inline_query_callback(bot: Bot, update: Update):
    query = update.inline_query  # type: InlineQuery
    result, pos = [], 0
    fetcher = get("rpc", "stub")  # type: WxFetcherStub
    prefix = get("prefix")
    while True:
        match = _REGEX_URL.search(query.query, pos)  # re.Match
        if match is None:
            result.append(query.query[pos:])
            break
        # Non-URL string
        result.append(query.query[pos : match.start()])
        # Fetch a shortened URL
        url = query.query[match.start() : match.end()]
        try:
            req = FetchURLRequest(url=url)
            fetch_resp = fetcher.FetchURL(req)  # type: FetchURLResponse
            url = "{}/{}".format(prefix, fetch_resp.key)
            print(fetch_resp)
        except RpcError as e:
            # pylint: disable=no-member
            details = e.details()
            if details == "unsupported url":
                pass
        except Exception:
            import traceback
            traceback.print_exc()
        finally:
            result.append(url)
        # Seek to match end
        pos = match.end()


wxmpbotInlineQueryHandler = InlineQueryHandler(wxmpbot_inline_query_callback)
