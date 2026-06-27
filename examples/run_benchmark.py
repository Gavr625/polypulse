"""Run the latency benchmark (equivalent to `python -m polypulse benchmark`)."""

import asyncio

from polypulse.benchmark import run_benchmark

asyncio.run(run_benchmark())
