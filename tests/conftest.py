"""Shared test doubles for the WebSocket feed."""

import asyncio


class FakeWS:
    """An async-iterable fake websocket yielding pre-scripted frames."""

    def __init__(self, frames):
        self._frames = list(frames)
        self.sent = []
        self.closed = False

    async def send(self, msg):
        self.sent.append(msg)

    async def close(self):
        self.closed = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        await asyncio.sleep(0)  # cooperative yield
        if self.closed or not self._frames:
            raise StopAsyncIteration
        return self._frames.pop(0)


class FakeConnect:
    """Async context manager returned by a fake ``websockets.connect``."""

    def __init__(self, ws):
        self.ws = ws

    async def __aenter__(self):
        return self.ws

    async def __aexit__(self, *exc):
        return False
