import pytest

from polypulse.benchmark import run_benchmark


@pytest.mark.integration
async def test_benchmark_runs_live():
    # Smoke test: should complete without raising against the live API.
    await run_benchmark()
