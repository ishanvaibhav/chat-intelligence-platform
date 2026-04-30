from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pandas as pd


MESSAGE_PATTERNS = (
    re.compile(
        r"^(?P<date>\d{1,2}/\d{1,2}/\d{2,4}),\s(?P<time>\d{1,2}:\d{2}(?:\s?[apAP][mM])?)\s-\s(?P<message>.*)$"
    ),
    re.compile(
        r"^(?P<date>\d{1,2}/\d{1,2}/\d{2,4}),\s(?P<time>\d{1,2}:\d{2}:\d{2})\s-\s(?P<message>.*)$"
    ),
)
SENDER_PATTERN = re.compile(r"^(?P<user>[^:]+):\s(?P<body>.*)$")


def _parse_datetime(date_str: str, time_str: str) -> datetime:
    formats = (
        "%d/%m/%y, %I:%M %p",
        "%d/%m/%Y, %I:%M %p",
        "%m/%d/%y, %I:%M %p",
        "%m/%d/%Y, %I:%M %p",
        "%d/%m/%y, %H:%M",
        "%d/%m/%Y, %H:%M",
        "%m/%d/%y, %H:%M",
        "%m/%d/%Y, %H:%M",
        "%d/%m/%y, %H:%M:%S",
        "%d/%m/%Y, %H:%M:%S",
        "%m/%d/%y, %H:%M:%S",
        "%m/%d/%Y, %H:%M:%S",
    )
    raw_value = f"{date_str}, {time_str}"

    for fmt in formats:
        try:
            return datetime.strptime(raw_value, fmt)
        except ValueError:
            continue

    raise ValueError(f"Unsupported WhatsApp datetime format: {raw_value}")


def _extract_message_parts(raw_message: str) -> tuple[str, str]:
    match = SENDER_PATTERN.match(raw_message)
    if match:
        return match.group("user").strip(), match.group("body").strip()
    return "group_notification", raw_message.strip()


def load_chat_file(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="ignore")


def preprocess_chat(data: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    current_message: dict[str, object] | None = None

    for raw_line in data.splitlines():
        line = raw_line.replace("\u200e", "").strip("\ufeff")
        matched = None

        for pattern in MESSAGE_PATTERNS:
            matched = pattern.match(line)
            if matched:
                break

        if matched:
            if current_message is not None:
                rows.append(current_message)

            parsed_date = _parse_datetime(matched.group("date"), matched.group("time"))
            user, message = _extract_message_parts(matched.group("message"))
            current_message = {
                "date": parsed_date,
                "user": user,
                "message": message,
            }
            continue

        if current_message is not None:
            current_message["message"] = f"{current_message['message']}\n{raw_line}".strip()

    if current_message is not None:
        rows.append(current_message)

    if not rows:
        return pd.DataFrame(columns=["date", "user", "message"])

    df = pd.DataFrame(rows)
    df["only_date"] = df["date"].dt.date
    df["year"] = df["date"].dt.year
    df["month_num"] = df["date"].dt.month
    df["month"] = df["date"].dt.month_name()
    df["day"] = df["date"].dt.day
    df["day_name"] = df["date"].dt.day_name()
    df["hour"] = df["date"].dt.hour
    df["minute"] = df["date"].dt.minute
    df["period"] = df["hour"].map(lambda hour: f"{hour:02d}-{((hour + 1) % 24):02d}")
    return df


def preprocess(data: str) -> pd.DataFrame:
    return preprocess_chat(data)
