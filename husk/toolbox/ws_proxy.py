"""Toolbox WebSocket reverse proxy.

Pumps frames bidirectionally between an authenticated client WebSocket
(facing the SDK / browser) and the daemon's WebSocket inside the sandbox.

Used for PTY sessions, streaming logs, and any other long-lived WS endpoint
exposed by the upstream daemon.
"""

from __future__ import annotations

import asyncio

import websockets
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
from websockets.exceptions import ConnectionClosed

from husk.core.config import settings
from husk.core.docker_client import DockerClient
from husk.sandbox.models import Sandbox


async def proxy_websocket(
    client_ws: WebSocket,
    sb: Sandbox,
    docker: DockerClient,
    path: str,
) -> None:
    """Bidirectional pump: client WS ↔ daemon WS."""
    if not sb.container_id:
        await client_ws.close(code=4409, reason="sandbox has no running container")
        return

    info = await docker.inspect(sb.container_id)
    if info is None or info.ip is None:
        await client_ws.close(code=4404, reason="container or IP not found")
        return

    upstream_url = f"ws://{info.ip}:{settings.daemon_port}/{path.lstrip('/')}"
    await client_ws.accept()

    try:
        async with websockets.connect(upstream_url) as upstream:
            await asyncio.gather(
                _client_to_upstream(client_ws, upstream),
                _upstream_to_client(client_ws, upstream),
                return_exceptions=True,
            )
    except (ConnectionClosed, WebSocketDisconnect):
        pass
    except Exception as e:  # pragma: no cover — connection-time failures
        logger.warning("ws proxy upstream error: {} {}", upstream_url, e)
        try:
            await client_ws.close(code=1011, reason="upstream error")
        except Exception:
            pass


async def _client_to_upstream(client_ws: WebSocket, upstream) -> None:
    try:
        while True:
            msg = await client_ws.receive()
            if msg["type"] == "websocket.disconnect":
                break
            if "text" in msg and msg["text"] is not None:
                await upstream.send(msg["text"])
            elif "bytes" in msg and msg["bytes"] is not None:
                await upstream.send(msg["bytes"])
    except (WebSocketDisconnect, ConnectionClosed):
        pass
    finally:
        await upstream.close()


async def _upstream_to_client(client_ws: WebSocket, upstream) -> None:
    try:
        async for frame in upstream:
            if isinstance(frame, bytes):
                await client_ws.send_bytes(frame)
            else:
                await client_ws.send_text(frame)
    except (WebSocketDisconnect, ConnectionClosed):
        pass
    finally:
        try:
            await client_ws.close()
        except Exception:
            pass
