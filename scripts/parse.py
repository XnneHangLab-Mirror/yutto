from __future__ import annotations

import argparse
import asyncio
import sys

from yutto.core.execution import RequestExecutionScopeFactory
from yutto.core.request import DownloadRequest
from yutto.download_manager import DownloadManager
from yutto.exceptions import ErrorCode, YuttoBaseException


async def parse(url: str) -> int:
    request = DownloadRequest.model_validate(
        {
            "source": {"url": url},
            "scope": {"batch": True},
            "network": {"proxy": "no"},
        }
    )
    result = await DownloadManager().execute_resolve(RequestExecutionScopeFactory(), [request])
    for index, item in enumerate(result.items, start=1):
        print(f"{index}. {item.name}\n   {item.url}\n   {item.planned_path}")
    print(
        f"共 {len(result.items)} 个条目，{len({str(item.avid) for item in result.items})} 个 BV，{len(result.failures)} 项失败"
    )
    for failure in result.failures:
        print(failure.message, file=sys.stderr)
    return ErrorCode.RESOLVE_FAILED_ERROR.value if result.failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="批量解析 B 站链接，只显示条目和计划路径，不下载资源。")
    parser.add_argument("url", nargs="?", default="https://www.bilibili.com/video/BV17zDWYwEj8/?p=2")
    args = parser.parse_args()
    try:
        return asyncio.run(parse(args.url))
    except YuttoBaseException as error:
        print(error.message, file=sys.stderr)
        return error.code.value
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
