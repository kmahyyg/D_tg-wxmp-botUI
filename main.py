import grpc
import json
import signal
from argparse import ArgumentParser
from telegram.ext import Updater as TelegramUpdater
from rpc import wxfetcher_pb2_grpc as rpc
from rpc.wxfetcher_pb2 import FetchURLRequest, FetchURLResponse
from handler import wxmpbotInlineQueryHandler
from storage import get, put
import storage

def load_config():
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", default="config.json", type=str)
    args = parser.parse_args()
    with open(args.config) as f:
        return json.load(f)

def signal_handler(signum, frame):
    get("tg", "updater").stop()
    get("rpc", "channel").close()

def main():
    # Load configuration
    cfg = load_config()
    # Initialize RPC and Telegram Bot
    rpc_channel = grpc.insecure_channel(cfg["fetcher"]["remote"])
    rpc_stub = rpc.WxFetcherStub(rpc_channel)
    tg_updater = TelegramUpdater(token=cfg["telegram"]["token"])
    tg_updater.dispatcher.add_handler(wxmpbotInlineQueryHandler)
    tg_updater.start_polling()
    # Set global storage
    put("rpc", "channel", rpc_channel)
    put("rpc", "stub", rpc_stub)
    put("tg", "updater", tg_updater)
    put("prefix", "{}{}".format("https://" if cfg["web"].get("https") else "http://", cfg["web"]["host"]))
    # Set signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    main()
