from __future__ import annotations

import runpy
from pathlib import Path

import pytest

from yutto.core.result import ResolvedItem, ResolveFailure, ResolveResult
from yutto.download_manager import DownloadManager
from yutto.exceptions import ErrorCode
from yutto.types import BvId, CId


@pytest.mark.parametrize("partial_failure", [False, True])
def test_parse_script_only_resolves(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], partial_failure: bool
):
    async def resolve(_manager, _factory, requests):
        assert requests[0].scope.batch
        assert requests[0].source.url.endswith("BV17zDWYwEj8/?p=2")
        return ResolveResult(
            items=(
                ResolvedItem(
                    avid=BvId("BV17zDWYwEj8"),
                    cid=CId("10"),
                    url="https://www.bilibili.com/video/BV17zDWYwEj8?p=2",
                    name="第二集",
                    title="测试",
                    cover_url="",
                    planned_path=Path("测试/第二集"),
                ),
            ),
            failures=(ResolveFailure(type="NotFoundError", message="视频不存在", code=17),) if partial_failure else (),
        )

    def unexpected(*_args, **_kwargs):
        pytest.fail("只解析脚本不应进入下载流程")

    monkeypatch.setattr(DownloadManager, "execute_resolve", resolve)
    monkeypatch.setattr(DownloadManager, "execute", unexpected)
    monkeypatch.setattr("sys.argv", ["parse.py"])
    with pytest.raises(SystemExit) as error:
        runpy.run_path(str(Path(__file__).parents[1] / "scripts" / "parse.py"), run_name="__main__")
    assert error.value.code == (ErrorCode.RESOLVE_FAILED_ERROR.value if partial_failure else 0)
    output = capsys.readouterr()
    assert "BV17zDWYwEj8?p=2" in output.out
    assert "共 1 个条目，1 个 BV" in output.out
    assert ("视频不存在" in output.err) == partial_failure
