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
        await asyncio.gather(task, return_exceptions=True)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "benchmark":
            asyncio.run(run_benchmark())
        elif args.command == "watch":
            asyncio.run(_watch(args.tokens))
        else:
            parser.print_help()
    except KeyboardInterrupt:
        pass
    return 0
