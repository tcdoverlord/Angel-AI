from __future__ import annotations

from datetime import datetime


def local_datetime() -> dict[str, str]:
    """Return a fresh, timezone-aware local clock snapshot."""
    now = datetime.now().astimezone()
    timezone_name = now.tzname() or str(now.tzinfo or "local time")
    return {
        "iso": now.isoformat(timespec="seconds"),
        "date": now.strftime("%A, %B %d, %Y"),
        "time": now.strftime("%I:%M:%S %p").lstrip("0"),
        "timezone": timezone_name,
    }


def format_local_datetime() -> str:
    data = local_datetime()
    return (
        f"Local date: {data['date']}\n"
        f"Local time: {data['time']}\n"
        f"Timezone: {data['timezone']}"
    )
