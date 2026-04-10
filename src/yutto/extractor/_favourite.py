from __future__ import annotations

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from yutto.api.ugc_video import UgcVideoListItem
    from yutto.utils.metadata import MetaData

FAVOURITE_SINGLE_PAGE_TEMPLATE = "{username}的收藏夹/{series_title}/{title}"
FAVOURITE_MULTI_PAGE_TEMPLATE = "{username}的收藏夹/{series_title}/{title}/{name}"


def format_multi_page_favourite_name(page_id: int, page_name: str) -> str:
    return f"P{page_id:02}_{page_name}"


def normalize_favourite_video_item(
    ugc_video_item: UgcVideoListItem,
    favourite_title: str,
    *,
    is_single_page_video: bool,
) -> tuple[UgcVideoListItem, str, str | None]:
    if not is_single_page_video:
        normalized_name = format_multi_page_favourite_name(ugc_video_item["id"], ugc_video_item["name"])
        metadata = cast(
            "MetaData",
            {
                **ugc_video_item["metadata"],
                "title": normalized_name,
                "show_title": normalized_name,
            },
        )
        normalized_item = cast(
            "UgcVideoListItem",
            {
                **ugc_video_item,
                "name": normalized_name,
                "metadata": metadata,
            },
        )
        return normalized_item, FAVOURITE_MULTI_PAGE_TEMPLATE, favourite_title

    metadata = cast(
        "MetaData",
        {
            **ugc_video_item["metadata"],
            "title": favourite_title,
            "show_title": favourite_title,
        },
    )
    normalized_item = cast(
        "UgcVideoListItem",
        {
            **ugc_video_item,
            "name": favourite_title,
            "metadata": metadata,
        },
    )
    return normalized_item, FAVOURITE_SINGLE_PAGE_TEMPLATE, None
