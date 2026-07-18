from __future__ import annotations

import inspect
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest
from returns.result import Success

import yutto.download_manager as download_manager_module
from yutto.core.events import DownloadItemListed, DownloadStage, DownloadStageChanged
from yutto.core.operation import bind_download_event_sink, notify_episode_listed
from yutto.core.request import DownloadRequest
from yutto.core.result import ResolvedItem
from yutto.download_manager import DownloadManager
from yutto.types import AId, CId, ResolvableEpisode
from yutto.utils.asynclib import CoroutineWrapper
from yutto.utils.fetcher import Fetcher, FetcherContext
from yutto.utils.functional import as_sync

if TYPE_CHECKING:
    import httpx

    from yutto.core.events import DownloadEvent
    from yutto.types import EpisodeData, EpisodeInfo, ExtractorOptions

pytestmark = pytest.mark.processor


def make_info(name: str, display_group: str | None = None) -> EpisodeInfo:
    return {
        "avid": AId("1"),
        "cid": CId("10"),
        "url": "https://www.bilibili.com/video/av1?p=1",
        "name": name,
        "title": "标题",
        "cover_url": "https://example.com/cover.jpg",
        "uploader": "某UP主",
        "description": "视频简介",
        "tags": ["标签A", "标签B"],
        "path": Path(f"标题/{name}"),
        "display_group": display_group,
    }


class RecordingEventSink:
    def __init__(self) -> None:
        self.events: list[DownloadEvent] = []

    def emit(self, event: DownloadEvent) -> None:
        self.events.append(event)


@as_sync
async def test_resolve_items_lists_stable_info_without_resolving_data(monkeypatch: pytest.MonkeyPatch):
    executed: list[str] = []

    async def resolve_episode() -> EpisodeData | None:
        executed.append("ran")
        return None

    data_coro = resolve_episode()
    info = make_info("P1", display_group="标题")
    resolvable = ResolvableEpisode(info=info, data_coro=CoroutineWrapper(data_coro))

    class FakeExtractor:
        def resolve_shortcut(self, url: str) -> tuple[bool, str]:
            return True, f"https://example.com/{url}"

        def match(self, url: str) -> bool:
            return url == "https://example.com/BV1baseline"

        async def __call__(
            self,
            ctx: FetcherContext,
            client: httpx.AsyncClient,
            options: ExtractorOptions,
        ) -> list[ResolvableEpisode | None]:
            return [None, resolvable]

    async def fake_validate_user_info(ctx: FetcherContext, requirements: dict[str, bool]) -> bool:
        return True

    async def fake_get_redirected_url(ctx: FetcherContext, client: httpx.AsyncClient, url: str):
        return Success(url)

    monkeypatch.setattr(download_manager_module, "UgcVideoExtractor", FakeExtractor)
    monkeypatch.setattr(download_manager_module, "validate_user_info", fake_validate_user_info)
    monkeypatch.setattr(Fetcher, "get_redirected_url", fake_get_redirected_url)

    manager = DownloadManager()
    sink = RecordingEventSink()
    client = cast("httpx.AsyncClient", object())
    request = DownloadRequest.model_validate({"source": {"url": "BV1baseline"}})

    with bind_download_event_sink(sink):
        items = await manager.resolve_items(client, FetcherContext(), request)

    expected_item = ResolvedItem(
        avid="1",
        cid="10",
        url="https://www.bilibili.com/video/av1?p=1",
        name="P1",
        title="标题",
        cover_url="https://example.com/cover.jpg",
        planned_path=Path("标题/P1"),
        display_group="标题",
        uploader="某UP主",
        description="视频简介",
        tags=("标签A", "标签B"),
    )
    assert items == [expected_item]
    # data 懒协程从未执行，且已被关闭，不会留下 un-awaited 警告
    assert executed == []
    assert inspect.getcoroutinestate(data_coro) == inspect.CORO_CLOSED
    assert sink.events == [
        DownloadStageChanged(name=DownloadStage.RESOLVING),
        DownloadItemListed(
            avid="1",
            cid="10",
            url="https://www.bilibili.com/video/av1?p=1",
            name="P1",
            title="标题",
            cover_url="https://example.com/cover.jpg",
            planned_path=Path("标题/P1"),
            display_group="标题",
            uploader="某UP主",
            description="视频简介",
            tags=("标签A", "标签B"),
        ),
    ]


@as_sync
async def test_resolve_items_streams_hooked_episodes_without_duplicates(monkeypatch: pytest.MonkeyPatch):
    """流式提取器经 notify_episode_listed 提前推送的条目不会被收尾补发重复。"""

    async def noop() -> EpisodeData | None:
        return None

    streamed = ResolvableEpisode(info=make_info("P1", display_group="标题"), data_coro=CoroutineWrapper(noop()))
    late = ResolvableEpisode(info=make_info("P2", display_group="标题"), data_coro=CoroutineWrapper(noop()))

    class FakeExtractor:
        def resolve_shortcut(self, url: str) -> tuple[bool, str]:
            return True, f"https://example.com/{url}"

        def match(self, url: str) -> bool:
            return url == "https://example.com/BV1stream"

        async def __call__(
            self,
            ctx: FetcherContext,
            client: httpx.AsyncClient,
            options: ExtractorOptions,
        ) -> list[ResolvableEpisode | None]:
            # 流式提取器：解析过程中先推送 P1；P2 留给 resolve_items 收尾补发
            notify_episode_listed(streamed)
            return [streamed, late]

    async def fake_validate_user_info(ctx: FetcherContext, requirements: dict[str, bool]) -> bool:
        return True

    async def fake_get_redirected_url(ctx: FetcherContext, client: httpx.AsyncClient, url: str):
        return Success(url)

    monkeypatch.setattr(download_manager_module, "UgcVideoExtractor", FakeExtractor)
    monkeypatch.setattr(download_manager_module, "validate_user_info", fake_validate_user_info)
    monkeypatch.setattr(Fetcher, "get_redirected_url", fake_get_redirected_url)

    manager = DownloadManager()
    sink = RecordingEventSink()
    client = cast("httpx.AsyncClient", object())
    request = DownloadRequest.model_validate({"source": {"url": "BV1stream"}})

    with bind_download_event_sink(sink):
        items = await manager.resolve_items(client, FetcherContext(), request)

    listed = [event for event in sink.events if isinstance(event, DownloadItemListed)]
    # 每条恰好一次：流式推送的 P1 在前（提取中），P2 收尾补发
    assert [event.name for event in listed] == ["P1", "P2"]
    # 返回列表保持提取器给出的顺序
    assert [item.name for item in items] == ["P1", "P2"]
    # 两个懒协程都被关闭
    assert inspect.getcoroutinestate(streamed.data_coro.coro) == inspect.CORO_CLOSED
    assert inspect.getcoroutinestate(late.data_coro.coro) == inspect.CORO_CLOSED
