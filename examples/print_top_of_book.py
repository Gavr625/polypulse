"""Print top-of-book for one token once the feed warms up."""

import asyncio

from polypulse import BookFeed

TOKEN = "REPLACE_WITH_A_CLOB_TOKEN_ID"


async def main() -> None:
    feed = BookFeed([TOKEN])
    asyncio.create_task(feed.run())
    await asyncio.sleep(2)
    print("bid", feed.best_bid(TOKEN), "ask", feed.best_ask(TOKEN), "mid", feed.mid(TOKEN))
    feed.stop()


asyncio.run(main())
