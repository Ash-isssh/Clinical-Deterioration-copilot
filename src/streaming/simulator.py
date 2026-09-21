"""
Async generator that produces synthetic vitals readings for one patient,
simulating a live stream rather than a static batch.
"""
import asyncio


async def vitals_stream(patient_id: str, readings: list[dict], interval: float = 1.0):
    """Yield one reading at a time with a delay, simulating arrival over time."""
    for reading in readings:
        yield reading
        await asyncio.sleep(interval)


# TODO: load readings from data/raw/ (synthetic ICU dataset) instead of a hardcoded list
