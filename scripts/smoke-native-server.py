from __future__ import annotations

import argparse
import contextlib
import importlib
import json
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
from typing import TYPE_CHECKING, NoReturn

from websockets.sync.client import connect

if TYPE_CHECKING:
    from collections.abc import TextIO

_LISTENING_URL = re.compile(r"ws://(?P<host>\[[^]]+\]|[^:\s]+):(?P<port>\d+)")
_REQUIRED_CAPABILITIES = {
    "download.start",
    "resolve.start",
    "task.cancel",
    "task.get",
    "task.subscribe",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ffmpeg-path", required=True)
    parser.add_argument("--timeout", type=float, default=30)
    return parser.parse_args()


def emit_lines(stream: TextIO, label: str, output: queue.Queue[tuple[str, str]]) -> None:
    try:
        for line in stream:
            output.put((label, line.rstrip()))
    finally:
        stream.close()


def json_rpc(connection, request_id: int, method: str, params: dict[str, object]) -> dict[str, object]:
    connection.send(json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}))
    response = json.loads(connection.recv(timeout=5))
    if not isinstance(response, dict):
        raise RuntimeError(f"unexpected JSON-RPC response: {response!r}")
    if "error" in response:
        raise RuntimeError(f"JSON-RPC {method} failed: {response['error']!r}")
    return response


def fail(message: str, logs: list[str]) -> NoReturn:
    details = "\n".join(logs[-20:]) or "no server output"
    raise RuntimeError(f"{message}\n{details}")


def main() -> None:
    args = parse_args()
    importlib.import_module("yutto._core")

    token = "native-wheel-smoke-token"
    environment = os.environ | {"YUTTO_SERVER_TOKEN": token}
    with tempfile.TemporaryDirectory(prefix="yutto-native-server-") as temporary_directory:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "yutto",
                "serve",
                "--port",
                "0",
                "--download-root",
                temporary_directory,
                "--ffmpeg-path",
                args.ffmpeg_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env=environment,
        )
        assert process.stdout is not None
        assert process.stderr is not None
        output: queue.Queue[tuple[str, str]] = queue.Queue()
        readers = [
            threading.Thread(target=emit_lines, args=(process.stdout, "stdout", output), daemon=True),
            threading.Thread(target=emit_lines, args=(process.stderr, "stderr", output), daemon=True),
        ]
        for reader in readers:
            reader.start()

        logs: list[str] = []
        uri: str | None = None
        deadline = time.monotonic() + args.timeout
        try:
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    fail(f"server exited with {process.returncode}", logs)
                try:
                    label, line = output.get(timeout=0.1)
                except queue.Empty:
                    continue
                logs.append(f"{label}: {line}")
                if label == "stdout" and (match := _LISTENING_URL.search(line)):
                    uri = match.group(0)
                    break

            if uri is None:
                fail("timed out waiting for server announce", logs)

            with connect(uri, proxy=None, open_timeout=5, close_timeout=5) as connection:
                authenticated = json_rpc(connection, 1, "server.authenticate", {"token": token})
                if authenticated.get("result") != {"authenticated": True}:
                    fail(f"unexpected authentication result: {authenticated!r}", logs)
                info = json_rpc(connection, 2, "server.info", {})
                result = info.get("result")
                if not isinstance(result, dict):
                    fail(f"unexpected server.info result: {info!r}", logs)
                capabilities = result.get("capabilities")
                if result.get("protocol_version") != 1 or not isinstance(capabilities, list):
                    fail(f"unexpected server.info result: {info!r}", logs)
                missing = _REQUIRED_CAPABILITIES.difference(capabilities)
                if missing:
                    fail(f"server is missing capabilities: {sorted(missing)!r}", logs)
        finally:
            if process.poll() is None:
                process.terminate()
                with contextlib.suppress(subprocess.TimeoutExpired):
                    process.wait(timeout=5)
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    main()
