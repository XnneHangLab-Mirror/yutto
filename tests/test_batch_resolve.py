from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, cast

import pytest

import yutto.extractor._batch as batch_module
from yutto.exceptions import MaxRetryError, NotFoundError
from yutto.extractor._batch import resolve_ugc_video_lists
from yutto.types import BvId
from yutto.utils.fetcher import FetcherContext
from yutto.utils.functional import as_sync

if TYPE_CHECKING:
    import httpx

    from yutto.api.ugc_video import UgcVideoList
    from yutto.types import AvId


def build_ugc_video_list(avid: AvId) -> UgcVideoList:
    return cast(
        "UgcVideoList",
        {
            "title": f"video-{avid}",
            "avid": avid,
            "pubdate": 1600000000,
            "pages": [],
        },
    )


class FakeFetcher:
    @staticmethod
    async def touch_url(ctx: FetcherContext, client: Any, url: str) -> None:
        return None


@pytest.mark.processor
@as_sync
async def test_resolve_preserves_order_and_isolates_failures(monkeypatch: Any):
    ok_avid_1 = BvId("BV1vZ4y1M7mQ")
    missing_avid = BvId("BV1missing")
    rate_limited_avid = BvId("BV1blocked")
    ok_avid_2 = BvId("BV1xx411c7mD")

    async def fake_get_ugc_video_list(ctx: FetcherContext, client: Any, avid: AvId) -> UgcVideoList:
        await asyncio.sleep(0)
        if avid is missing_avid:
            raise NotFoundError(f"啊叻？视频 {avid} 不见了诶")
        if avid is rate_limited_avid:
            raise MaxRetryError("超出最大重试次数！")
        return build_ugc_video_list(avid)

    monkeypatch.setattr(batch_module, "get_ugc_video_list", fake_get_ugc_video_list)
    monkeypatch.setattr(batch_module, "Fetcher", FakeFetcher)

    ctx = FetcherContext()
    client = cast("httpx.AsyncClient", None)
    results = await resolve_ugc_video_lists(ctx, client, [ok_avid_1, missing_avid, rate_limited_avid, ok_avid_2])

    assert len(results) == 4
    first, second, third, fourth = results
    assert first is not None
    assert first["avid"] is ok_avid_1
    assert second is None
    assert third is None
    assert fourth is not None
    assert fourth["avid"] is ok_avid_2


@pytest.mark.processor
@as_sync
async def test_resolve_concurrency_bounded_by_fetch_semaphore(monkeypatch: Any):
    max_workers = 2
    current = 0
    peak = 0

    async def fake_get_ugc_video_list(ctx: FetcherContext, client: Any, avid: AvId) -> UgcVideoList:
        nonlocal current, peak
        # 模拟真实 get_ugc_video_list 内部经过 fetch_guard 的请求
        async with ctx.fetch_guard():
            current += 1
            peak = max(peak, current)
            await asyncio.sleep(0.01)
            current -= 1
        return build_ugc_video_list(avid)

    monkeypatch.setattr(batch_module, "get_ugc_video_list", fake_get_ugc_video_list)
    monkeypatch.setattr(batch_module, "Fetcher", FakeFetcher)

    ctx = FetcherContext()
    ctx.set_fetch_semaphore(fetch_workers=max_workers)
    client = cast("httpx.AsyncClient", None)

    avids: list[AvId] = [BvId(f"BV1number{i:02}") for i in range(10)]
    results = await resolve_ugc_video_lists(ctx, client, avids)

    assert all(result is not None for result in results)
    assert peak == max_workers
