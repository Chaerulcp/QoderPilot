"""Local HTTP CONNECT relay for applications that cannot authenticate a proxy."""

from __future__ import annotations

import argparse
import base64
import ctypes
import os
import select
import socket
import socketserver
import ssl
import threading
import time
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlsplit


MAX_HEADER_BYTES = 64 * 1024


def _read_headers(connection: socket.socket) -> tuple[bytes, bytes]:
    data = bytearray()
    while b"\r\n\r\n" not in data:
        chunk = connection.recv(8192)
        if not chunk:
            return bytes(data), b""
        data.extend(chunk)
        if len(data) > MAX_HEADER_BYTES:
            raise ValueError("Proxy request headers are too large")
    header, remainder = bytes(data).split(b"\r\n\r\n", 1)
    return header + b"\r\n\r\n", remainder


def _with_proxy_authorization(headers: bytes, authorization: str) -> bytes:
    lines = headers.rstrip(b"\r\n").split(b"\r\n")
    filtered = [
        line
        for line in lines
        if not line.lower().startswith(b"proxy-authorization:")
    ]
    filtered.append(f"Proxy-Authorization: {authorization}".encode("ascii"))
    return b"\r\n".join(filtered) + b"\r\n\r\n"


class AuthenticatedProxyBridge(socketserver.ThreadingTCPServer):
    """Forward a local unauthenticated proxy endpoint to one authenticated proxy."""

    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, address: tuple[str, int], upstream_url: str) -> None:
        parsed = urlsplit(upstream_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Only HTTP/HTTPS upstream proxies are supported")
        if parsed.username is None:
            raise ValueError("The upstream proxy does not contain a username")

        self.upstream_host = parsed.hostname
        self.upstream_port = parsed.port or (443 if parsed.scheme == "https" else 80)
        self.upstream_tls = parsed.scheme == "https"
        username = unquote(parsed.username)
        password = unquote(parsed.password or "")
        credentials = base64.b64encode(
            f"{username}:{password}".encode("utf-8")
        ).decode("ascii")
        self.authorization = f"Basic {credentials}"
        super().__init__(address, ProxyBridgeHandler)

    def open_upstream(self) -> socket.socket:
        connection = socket.create_connection(
            (self.upstream_host, self.upstream_port),
            timeout=30,
        )
        if not self.upstream_tls:
            return connection
        context = ssl.create_default_context()
        return context.wrap_socket(connection, server_hostname=self.upstream_host)


class ProxyBridgeHandler(socketserver.BaseRequestHandler):
    server: AuthenticatedProxyBridge

    def handle(self) -> None:
        downstream = self.request
        downstream.settimeout(60)
        try:
            request_headers, request_body = _read_headers(downstream)
            if not request_headers:
                return
            first_line = request_headers.split(b"\r\n", 1)[0]
            method = first_line.split(b" ", 1)[0].upper()
            upstream = self.server.open_upstream()
            try:
                upstream.settimeout(60)
                upstream.sendall(
                    _with_proxy_authorization(
                        request_headers,
                        self.server.authorization,
                    )
                    + request_body
                )
                if method == b"CONNECT":
                    response_headers, response_body = _read_headers(upstream)
                    downstream.sendall(response_headers + response_body)
                    status = response_headers.split(b"\r\n", 1)[0].split()
                    if len(status) < 2 or status[1] != b"200":
                        return
                self._relay(downstream, upstream)
            finally:
                upstream.close()
        except (OSError, ValueError):
            return

    @staticmethod
    def _relay(left: socket.socket, right: socket.socket) -> None:
        peers = {left: right, right: left}
        while True:
            try:
                readable, _, _ = select.select(list(peers), [], [], 60)
            except OSError:
                return
            if not readable:
                continue
            for source in readable:
                try:
                    chunk = source.recv(65536)
                    if not chunk:
                        return
                    peers[source].sendall(chunk)
                except OSError:
                    return


def _pid_is_running(process_id: int) -> bool:
    if os.name != "nt":
        try:
            os.kill(process_id, 0)
        except OSError:
            return False
        return True

    process_query_limited_information = 0x1000
    still_active = 259
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(
        process_query_limited_information,
        False,
        process_id,
    )
    if not handle:
        return False
    try:
        exit_code = ctypes.c_ulong()
        return bool(kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))) and (
            exit_code.value == still_active
        )
    finally:
        kernel32.CloseHandle(handle)


def _monitor_targets(
    server: AuthenticatedProxyBridge,
    control_file: Path,
    launch_timeout: int,
) -> None:
    deadline = time.monotonic() + launch_timeout
    armed = False
    while True:
        try:
            values = control_file.read_text(encoding="utf-8").splitlines()
            process_ids = [int(value) for value in values if value.strip().isdigit()]
        except OSError:
            process_ids = []

        if process_ids:
            armed = True
            if not any(_pid_is_running(process_id) for process_id in process_ids):
                server.shutdown()
                return
        elif not armed and time.monotonic() >= deadline:
            server.shutdown()
            return
        time.sleep(2)


def serve(
    listen_host: str,
    listen_port: int,
    upstream_url: str,
    control_file: Path,
    launch_timeout: int = 120,
) -> None:
    with AuthenticatedProxyBridge((listen_host, listen_port), upstream_url) as server:
        monitor = threading.Thread(
            target=_monitor_targets,
            args=(server, control_file, launch_timeout),
            daemon=True,
        )
        monitor.start()
        try:
            server.serve_forever(poll_interval=0.5)
        finally:
            try:
                control_file.unlink(missing_ok=True)
            except OSError:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--listen-host", default="127.0.0.1")
    parser.add_argument("--listen-port", required=True, type=int)
    parser.add_argument("--control-file", required=True, type=Path)
    parser.add_argument("--launch-timeout", default=120, type=int)
    args = parser.parse_args()
    upstream_url = os.getenv("QODERPILOT_PROXY_BRIDGE_UPSTREAM", "")
    if not upstream_url:
        return 2
    serve(
        args.listen_host,
        args.listen_port,
        upstream_url,
        args.control_file,
        args.launch_timeout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
