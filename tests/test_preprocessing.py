from __future__ import annotations

from pathlib import Path

from chat_analyser.preprocessing import preprocess_chat


def test_preprocess_handles_multiline_and_group_notifications():
    sample_path = Path(__file__).resolve().parent / "fixtures" / "sample_chat.txt"
    df = preprocess_chat(sample_path.read_text(encoding="utf-8"))

    assert df.shape[0] == 5
    assert df.loc[3, "user"] == "group_notification"
    assert "second line" in df.loc[4, "message"]
    assert set(["date", "user", "message", "period"]).issubset(df.columns)
