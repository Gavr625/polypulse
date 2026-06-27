"""React to every book update via a callback."""

import asyncio

from polypulse import BookFeed

TOKEN = "REPLACE_WITH_A_CLOB_TOKEN_ID"


def on_update(token_id: str, event: dict) -> None:
    print(event["event_type"], token_id)


async def main() -> None:
    feed = BookFeed([TOKEN], on_update=on_update)
    await asyncio.gather(feed.run())


asyncio.run(main())
