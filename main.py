import grpc
import json
import signal
import logging
from datetime import datetime
from argparse import ArgumentParser
from telegram.ext import Updater as TelegramUpdater
from proto import wxfetcher_pb2_grpc as proto
from handler import wxmpbotInlineQueryHandler
from storage import get, put


class LogFormatter(logging.Formatter):
    COLOR = {
        "DEBUG": 34,  # Blue
        "INFO": 32,  # Green
        "WARNING": 33,  # Yellow
        "ERROR": 31,  # Red
        "CRITICAL": 35,  # Magenta
    }

    def format(self, record: logging.LogRecord):
        log_str = "{} {}/ [{}] {}\n{}".format(
            datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S %Z"),
            record.levelname[0],
            record.name,
            record.getMessage(),
            self.formatException(record.exc_info)
            if record.exc_info is not None
            else "",
        ).strip()
        color_code = self.COLOR.get(record.levelname, 0)
        return "\33[{}m{}\33[0m".format(color_code, log_str)


def load_config():
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", default="config.json", type=str)
    args = parser.parse_args()
    with open(args.config) as f:
        return json.load(f)


def signal_handler(signum, frame):
    import sys
    sys.exit(0)
    get("tg", "updater").stop()
    get("rpc", "channel").close()

def main():
    # Load configuration
    cfg = load_config()
    # Initialize RPC and Telegram Bot
    rpc_channel = grpc.insecure_channel(cfg["fetcher"]["remote"])
    rpc_stub = proto.WxFetcherStub(rpc_channel)
    tg_updater = TelegramUpdater(token=cfg["telegram"]["token"])
    tg_updater.dispatcher.add_handler(wxmpbotInlineQueryHandler)
    tg_updater.start_polling()
    # Set global storage
    put("rpc", "channel", rpc_channel)
    put("rpc", "stub", rpc_stub)
    put("tg", "updater", tg_updater)
    put(
        "prefix",
        "{}{}".format(
            "https://" if cfg["web"].get("https") else "http://", cfg["web"]["host"]
        ),
    )
    # Set signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


if __name__ == "__main__":
    main()
