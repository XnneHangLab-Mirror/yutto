from __future__ import annotations

from typing import TYPE_CHECKING, cast

from yutto.extractor._favourite import (
    FAVOURITE_MULTI_PAGE_TEMPLATE,
    FAVOURITE_SINGLE_PAGE_TEMPLATE,
    normalize_favourite_video_item,
)
from yutto.types import BvId, CId

if TYPE_CHECKING:
    from yutto.api.ugc_video import UgcVideoListItem
    from yutto.utils.metadata import MetaData


def build_ugc_video_item(name: str, *, id: int = 1) -> UgcVideoListItem:
    metadata = cast(
        "MetaData",
        {
            "title": name,
            "show_title": name,
            "plot": "desc",
            "thumb": "https://example.com/cover.jpg",
            "premiered": 1710000000,
            "dateadded": 1710000100,
            "actor": [],
            "genre": [],
            "tag": [],
            "source": "",
            "original_filename": "",
            "website": "https://www.bilibili.com/video/BV1vZ4y1M7mQ",
            "chapter_info_data": [],
        },
    )
    return cast(
        "UgcVideoListItem",
        {
            "id": id,
            "name": name,
            "url": "https://www.bilibili.com/video/BV1vZ4y1M7mQ?p=1",
            "avid": BvId("BV1vZ4y1M7mQ"),
            "cid": CId("222190584"),
            "metadata": metadata,
        },
    )


def test_normalize_favourite_video_item_uses_favourite_title_for_single_page_video():
    ugc_video_item = build_ugc_video_item("mmexport1768031333059")

    resolved_item, auto_subpath_template, display_group = normalize_favourite_video_item(
        ugc_video_item,
        "收藏夹里看到的标题",
        is_single_page_video=True,
    )

    assert resolved_item["name"] == "收藏夹里看到的标题"
    assert resolved_item["metadata"]["title"] == "收藏夹里看到的标题"
    assert resolved_item["metadata"]["show_title"] == "收藏夹里看到的标题"
    assert auto_subpath_template == FAVOURITE_SINGLE_PAGE_TEMPLATE
    assert display_group is None


def test_normalize_favourite_video_item_prefixes_multi_page_video_name():
    ugc_video_item = build_ugc_video_item("手机端添加分p", id=2)

    resolved_item, auto_subpath_template, display_group = normalize_favourite_video_item(
        ugc_video_item,
        "收藏夹多 P 标题",
        is_single_page_video=False,
    )

    assert resolved_item["name"] == "P02_手机端添加分p"
    assert resolved_item["metadata"]["title"] == "P02_手机端添加分p"
    assert resolved_item["metadata"]["show_title"] == "P02_手机端添加分p"
    assert auto_subpath_template == FAVOURITE_MULTI_PAGE_TEMPLATE
    assert display_group == "收藏夹多 P 标题"
