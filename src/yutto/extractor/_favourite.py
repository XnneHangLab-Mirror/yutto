from __future__ import annotations

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from yutto.api.ugc_video import UgcVideoListItem
    from yutto.utils.metadata import MetaData

FAVOURITE_SINGLE_PAGE_TEMPLATE = "{username}的收藏夹/{series_title}/{title}"
FAVOURITE_MULTI_PAGE_TEMPLATE = "{username}的收藏夹/{series_title}/{title}/{name}"


def normalize_favourite_video_item(
    ugc_video_item: UgcVideoListItem,
    favourite_title: str,
    *,
    is_single_page_video: bool,
) -> tuple[UgcVideoListItem, str]:
    if not is_single_page_video:
        return ugc_video_item, FAVOURITE_MULTI_PAGE_TEMPLATE

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
    return normalized_item, FAVOURITE_SINGLE_PAGE_TEMPLATE
