from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from yutto.api.ugc_video import get_ugc_video_list
from yutto.exceptions import MaxRetryError, NoAccessPermissionError, NotFoundError
from yutto.utils.console.logger import Logger
from yutto.utils.fetcher import Fetcher
from yutto.utils.filter import Filter

if TYPE_CHECKING:
    import httpx

    from yutto.api.ugc_video import UgcVideoList
    from yutto.types import AvId
    from yutto.utils.fetcher import FetcherContext


async def resolve_ugc_video_lists(
    ctx: FetcherContext, client: httpx.AsyncClient, avids: list[AvId]
) -> list[UgcVideoList | None]:
    """并发解析一批视频的分 p 列表，结果顺序与 avids 一致

    并发在途请求数由 ctx 的 fetch_semaphore（--fetch-workers）控制；
    被时间过滤或解析失败（NotFoundError / NoAccessPermissionError / MaxRetryError）
    的视频以 None 占位，不会中断整批解析，其余未预期的异常仍会向外抛出。
    """

    async def resolve_one(avid: AvId) -> UgcVideoList | None:
        try:
            ugc_video_list = await get_ugc_video_list(ctx, client, avid)
            if not Filter.verify_timer(ugc_video_list["pubdate"]):
                Logger.debug(f"因为发布时间为 {ugc_video_list['pubdate']}，跳过 {ugc_video_list['title']}")
                return None
            # 在使用 SESSDATA 时，如果不去事先 touch 一下视频链接的话，是无法获取 episode_data 的
            await Fetcher.touch_url(ctx, client, avid.to_url())
        except (NotFoundError, NoAccessPermissionError) as e:
            Logger.error(e.message)
            return None
        except MaxRetryError as e:
            Logger.error(f"视频 {avid} 解析失败（{e.message}），已跳过～")
            return None
        return ugc_video_list

    return await asyncio.gather(*(resolve_one(avid) for avid in avids))
