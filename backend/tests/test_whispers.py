"""Whisper tests — send, paginate, redact."""
import pytest


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_send_and_list_whispers(client, make_token):
    t = await make_token("wh_send@test.com")
    r = await client.post("/seances", json={"name": "Whisper Test"}, headers=auth(t))
    sid = r.json()["id"]

    # Post a whisper via REST
    r = await client.post(f"/seances/{sid}/whispers",
                          json={"content": "Hello darkness"}, headers=auth(t))
    assert r.status_code == 201
    wid = r.json()["id"]

    r = await client.get(f"/seances/{sid}/whispers", headers=auth(t))
    assert r.status_code == 200
    items = r.json()["items"]
    assert any(w["id"] == wid for w in items)


@pytest.mark.asyncio
async def test_whisper_pagination(client, make_token):
    t = await make_token("wh_page@test.com")
    r = await client.post("/seances", json={"name": "Page Test"}, headers=auth(t))
    sid = r.json()["id"]

    # Post 5 whispers
    ids = []
    for i in range(5):
        r = await client.post(f"/seances/{sid}/whispers",
                               json={"content": f"msg {i}"}, headers=auth(t))
        ids.append(r.json()["id"])

    # Fetch newest 3
    r = await client.get(f"/seances/{sid}/whispers?limit=3", headers=auth(t))
    page = r.json()
    assert len(page["items"]) == 3
    assert page["next_before_id"] is not None

    # Fetch next page
    before = page["next_before_id"]
    r = await client.get(f"/seances/{sid}/whispers?limit=3&before_id={before}", headers=auth(t))
    page2 = r.json()
    assert len(page2["items"]) == 2  # 5 total, 3 fetched, 2 remaining
    assert page2["next_before_id"] is None


@pytest.mark.asyncio
async def test_redact_whisper(client, make_token):
    warden = await make_token("wh_redact_w@test.com")
    attendant = await make_token("wh_redact_a@test.com")

    r = await client.post("/seances", json={"name": "Redact Test"}, headers=auth(warden))
    sid = r.json()["id"]
    await client.post(f"/seances/{sid}/enter", headers=auth(attendant))

    # Attendant sends a whisper via REST
    r = await client.post(f"/seances/{sid}/whispers",
                          json={"content": "bad words"}, headers=auth(attendant))
    wid = r.json()["id"]

    # Attendant cannot redact (403)
    r = await client.delete(f"/seances/{sid}/whispers/{wid}", headers=auth(attendant))
    assert r.status_code == 403

    # Warden redacts (204)
    r = await client.delete(f"/seances/{sid}/whispers/{wid}", headers=auth(warden))
    assert r.status_code == 204

    # Whisper now shows as deleted in listing
    r = await client.get(f"/seances/{sid}/whispers", headers=auth(warden))
    item = next(w for w in r.json()["items"] if w["id"] == wid)
    assert item["is_deleted"] is True
    assert item["content"] == "⸻ withdrawn ⸻"


@pytest.mark.asyncio
async def test_attendant_cannot_whisper_without_presence(client, make_token):
    a = await make_token("wh_nopresence@test.com")
    b = await make_token("wh_nopresence2@test.com")

    r = await client.post("/seances", json={"name": "No Presence Test"}, headers=auth(a))
    sid = r.json()["id"]

    # b has no presence
    r = await client.post(f"/seances/{sid}/whispers",
                          json={"content": "ghost whisper"}, headers=auth(b))
    assert r.status_code == 403
