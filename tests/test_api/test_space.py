from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from yutto.api.space import (
    get_all_favourites,
    get_favourite_avids,
    get_favourite_info,
    get_medialist_avids,
    get_medialist_title,
    get_user_name,
    get_user_space_all_videos_avids,
)
from yutto.types import AId, BvId, FId, MId, SeriesId
from yutto.utils.fetcher import FetcherContext, create_client
from yutto.utils.functional import as_sync

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.api
@pytest.mark.ignore
@as_sync
async def test_get_user_space_all_videos_avids():
    mid = MId("100969474")
    ctx = FetcherContext()
    async with create_client() as client:
        all_avid = await get_user_space_all_videos_avids(ctx, client, mid=mid)
        assert len(all_avid) > 0
        assert AId("371660125") in all_avid or BvId("BV1vZ4y1M7mQ") in all_avid


@pytest.mark.api
@pytest.mark.ignore
@as_sync
async def test_get_user_name():
    mid = MId("100969474")
    ctx = FetcherContext()
    async with create_client() as client:
        username = await get_user_name(ctx, client, mid=mid)
        assert username == "时雨千陌"


@pytest.mark.api
@as_sync
async def test_get_favourite_info():
    fid = FId("1306978874")
    ctx = FetcherContext()
    async with create_client() as client:
        fav_info = await get_favourite_info(ctx, client, fid=fid)
        assert fav_info["fid"] == fid
        assert fav_info["title"] == "Test"


@pytest.mark.api
@as_sync
async def test_get_favourite_avids():
    fid = FId("1306978874")
    ctx = FetcherContext()
    async with create_client() as client:
        avids = await get_favourite_avids(ctx, client, fid=fid)
        assert AId("456782499") in avids or BvId("BV1o541187Wh") in avids


@as_sync
async def test_get_favourite_items_paginates_and_preserves_titles(monkeypatch: pytest.MonkeyPatch):
    import yutto.api.space as space_module

    fid = FId("1306978874")
    calls: list[str] = []
    client = cast("AsyncClient", object())

    async def fake_fetch_json(
        ctx: FetcherContext,
        client: object,
        url: str,
        *,
        params: dict[str, str] | None = None,
    ):
        assert params is None
        calls.append(url)
        if "pn=1" in url:
            return {
                "data": {
                    "has_more": True,
                    "medias": [
                        {"type": 2, "bvid": "BV1o541187Wh", "title": "收藏夹单集标题", "page": 1},
                        {"type": 12, "bvid": "BV1ignore", "title": "非视频资源", "page": 1},
                    ],
                }
            }
        if "pn=2" in url:
            return {
                "data": {
                    "has_more": False,
                    "medias": [
                        {"type": 2, "bvid": "BV1Y441167U2", "title": "收藏夹多 P 标题", "page": 2},
                    ],
                }
            }
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(space_module.Fetcher, "fetch_json", fake_fetch_json)

    favourite_items = await space_module.get_favourite_items(FetcherContext(), client, fid)

    assert favourite_items == [
        {"avid": BvId("BV1o541187Wh"), "title": "收藏夹单集标题", "page": 1},
        {"avid": BvId("BV1Y441167U2"), "title": "收藏夹多 P 标题", "page": 2},
    ]
    assert len(calls) == 2


@pytest.mark.api
@as_sync
async def test_all_favourites():
    mid = MId("100969474")
    ctx = FetcherContext()
    async with create_client() as client:
        fav_list = await get_all_favourites(ctx, client, mid=mid)
        assert {"fid": FId("1306978874"), "title": "Test"} in fav_list


@pytest.mark.api
@as_sync
async def test_get_medialist_avids():
    series_id = SeriesId("1947439")
    mid = MId("100969474")
    ctx = FetcherContext()
    async with create_client() as client:
        avids = await get_medialist_avids(ctx, client, series_id=series_id, mid=mid)
        assert avids == [BvId("BV1Y441167U2"), BvId("BV1vZ4y1M7mQ")]


@pytest.mark.api
@as_sync
async def test_get_medialist_title():
    series_id = SeriesId("1947439")
    ctx = FetcherContext()
    async with create_client() as client:
        title = await get_medialist_title(ctx, client, series_id=series_id)
        assert title == "一个小视频列表～"
