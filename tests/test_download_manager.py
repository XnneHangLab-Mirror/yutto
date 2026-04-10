from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import yutto.download_manager as download_manager_module

if TYPE_CHECKING:
    from yutto.types import EpisodeData


def build_episode_data(*, display_name: str, display_group: str | None) -> EpisodeData:
    return cast(
        "EpisodeData",
        {
            "url": "https://www.bilibili.com/video/BV1vZ4y1M7mQ?p=1",
            "videos": [],
            "audios": [],
            "subtitles": [],
            "metadata": None,
            "danmaku": {"save_type": "xml", "data": b""},
            "cover_data": None,
            "cover_link": None,
            "chapter_info_data": [],
            "path": Path(display_name),
            "display_name": display_name,
            "display_group": display_group,
        },
    )


def test_show_batch_episode_title_prints_group_header_once(monkeypatch: Any):
    messages: list[str] = []

    def fake_custom(message: str, badge: object, *args: object, **kwargs: object) -> None:
        messages.append(message)

    monkeypatch.setattr(download_manager_module.Logger, "custom", fake_custom)

    current_group = None
    current_group = download_manager_module.show_batch_episode_title(
        build_episode_data(display_name="P01_主标题", display_group="主标题"),
        1,
        3,
        current_group,
    )
    current_group = download_manager_module.show_batch_episode_title(
        build_episode_data(display_name="P02_叶子标题", display_group="主标题"),
        2,
        3,
        current_group,
    )

    assert messages == [
        "主标题",
        "  P01_主标题",
        "  P02_叶子标题",
    ]
    assert current_group == "主标题"
