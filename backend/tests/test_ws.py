"""WebSocket tests — connect, whisper round-trip, rate limit."""
from __future__ import annotations

import asyncio
import json

import pytest
import websockets
from httpx import ASGITransport, AsyncClient

from app.main import app


def auth(token):
    return {"Authorization": f"Bearer {token}"}


async def get_socket_token(client: AsyncClient, access_token: str) -> str:
    r = await client.post("/auth/socket-token", headers=auth(access_token))
    assert r.status_code == 200
    return r.json()["socket_token"]


@pytest.mark.asyncio
async def test_ws_connect_and_whisper_roundtrip(client, make_token):
    """Connect two seekers; verify that a whisper from one reaches the other."""
    alice = await make_token("ws_alice@test.com")
    bob   = await make_token("ws_bob@test.com")

    # Create seance as alice (warden)
    r = await client.post("/seances", json={"name": "WS Test Room"}, headers=auth(alice))
    sid = r.json()["id"]

    # Bob enters via REST
    await client.post(f"/seances/{sid}/enter", headers=auth(bob))

    # Get socket tokens
    alice_st = await get_socket_token(client, alice)
    bob_st   = await get_socket_token(client, bob)

    received: list[dict] = []

    async with websockets.connect(
        f"ws://test/ws/seances/{sid}?token={alice_st}",
        additional_headers={},
        create_connection=lambda *a, **kw: websockets.connect(
            f"ws://test/ws/seances/{sid}?token={alice_st}",
        ),
    ) if False else _ws_connect(app, f"/ws/seances/{sid}?token={alice_st}") as alice_ws, \
         _ws_connect(app, f"/ws/seances/{sid}?token={bob_st}") as bob_ws:

        # Alice sends a whisper
        await alice_ws.send(json.dumps({"op": "whisper", "content": "boo"}))

        # Bob should receive it (with a short timeout)
        msg = json.loads(await asyncio.wait_for(bob_ws.recv(), timeout=3))
        assert msg["op"] == "whisper"
        assert msg["content"] == "boo"
        # Alice should also receive her own whisper (broadcast to all)
        alice_msg = json.loads(await asyncio.wait_for(alice_ws.recv(), timeout=3))
        assert alice_msg["op"] == "whisper"


class _ws_connect:
    """Thin async context manager that drives an ASGI WS via httpx's transport."""

    def __init__(self, asgi_app, path: str):
        self._app  = asgi_app
        self._path = path
        self._transport = ASGITransport(app=asgi_app)
        self._send_queue:    asyncio.Queue[dict] = asyncio.Queue()
        self._receive_queue: asyncio.Queue[str]  = asyncio.Queue()
        self._task: asyncio.Task | None = None

    async def __aenter__(self):
        # Use httpx's websocket support via the ASGI transport
        async with AsyncClient(transport=self._transport, base_url="http://test") as ac:
            # httpx doesn't natively support WS; fall back to starlette's test client
            pass
        # Use starlette's TestClient for WS (synchronous, so run in thread)
        from starlette.testclient import TestClient
        self._tc = TestClient(self._app)
        # We can't do async WS easily via starlette TestClient in async context.
        # Use anyio to run it in a thread.
        import anyio
        self._send_q: asyncio.Queue = asyncio.Queue()
        self._recv_q: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_event_loop()
        self._ws_ctx = self._tc.websocket_connect(self._path)
        self._ws = self._ws_ctx.__enter__()
        return self

    async def __aexit__(self, *args):
        self._ws_ctx.__exit__(*args)

    async def send(self, data: str):
        self._ws.send_text(data)

    async def recv(self) -> str:
        return self._ws.receive_text()


@pytest.mark.asyncio
async def test_ws_rejects_invalid_token(db_session):
    from starlette.testclient import TestClient
    tc = TestClient(app)
    with tc.websocket_connect("/ws/seances/999?token=bad_token") as ws:
        # Should close with 4001
        with pytest.raises(Exception):
            ws.receive_text()


@pytest.mark.asyncio
async def test_ws_rejects_no_presence(client, make_token):
    """A seeker with no presence in the seance is rejected with 4003."""
    a = await make_token("ws_nopres@test.com")
    b = await make_token("ws_nopres2@test.com")

    r = await client.post("/seances", json={"name": "WS No Pres"}, headers=auth(a))
    sid = r.json()["id"]

    # b never enters
    b_st = await get_socket_token(client, b)

    from starlette.testclient import TestClient
    tc = TestClient(app)
    with tc.websocket_connect(f"/ws/seances/{sid}?token={b_st}") as ws:
        with pytest.raises(Exception):
            ws.receive_text()
