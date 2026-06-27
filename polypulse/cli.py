"""Command-line interface: `polypulse benchmark` and `polypulse watch`."""

from __future__ import annotations

import argparse
import asyncio

from .benchmark import run_benchmark
from .feed import BookFeed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="polypulse", description="Real-time Polymarket order-book feed."
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("benchmark", help="measure WS push vs REST /book latency on a live market")
    watch = sub.add_parser("watch", help="stream and print top-of-book for token ids")
    watch.add_argument("tokens", nargs="+", help="one or more CLOB token ids")
    return parser


async def _watch(tokens: list[str]) -> None:
    feed = BookFeed(tokens)
    task = asyncio.create_task(feed.run())
    try:
        while True:
            await asyncio.sleep(1.0)
            for t in tokens:
                print(
                    f"{t[:10]}…  bid={feed.best_bid(t)}  ask={feed.best_ask(t)}  "
                    f"mid={feed.mid(t)}  src={feed.source(t)}"
                )
    finally:
        feed.stop()
        task.cancel()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "benchmark":
        asyncio.run(run_benchmark())
    elif args.command == "watch":
        try:
            asyncio.run(_watch(args.tokens))
        except KeyboardInterrupt:
            pass
    else:
        build_parser().print_help()
    return 0
