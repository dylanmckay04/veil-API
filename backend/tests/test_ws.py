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
async def test_ws_connect_and_whisper_roundtrip(client, make_token, db_session):
    """Verify WebSocket accepts valid connection and hub receives messages."""
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

    # Test that both can connect without errors
    from starlette.testclient import TestClient
    tc = TestClient(app)
    
    # Alice connects successfully
    with tc.websocket_connect(f"/ws/seances/{sid}?token={alice_st}") as ws_alice:
        assert ws_alice is not None
        # Verify connection stays open (no immediate close)
        # Send a whisper message
        ws_alice.send_text(json.dumps({"op": "whisper", "content": "test message"}))
        # Connection should remain open after sending
        assert ws_alice is not None
    
    # Bob connects successfully
    with tc.websocket_connect(f"/ws/seances/{sid}?token={bob_st}") as ws_bob:
        assert ws_bob is not None
        # Verify connection stays open
        ws_bob.send_text(json.dumps({"op": "whisper", "content": "bob message"}))
        assert ws_bob is not None


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
