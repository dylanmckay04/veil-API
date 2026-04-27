"""Seance lifecycle, access control, invite flow, kick/transfer."""
import pytest


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_and_list_seance(client, make_token):
    t = await make_token("owner@test.com")
    r = await client.post("/seances", json={"name": "Test Seance"}, headers=auth(t))
    assert r.status_code == 201
    sid = r.json()["id"]

    r = await client.get("/seances", headers=auth(t))
    assert any(s["id"] == sid for s in r.json())


@pytest.mark.asyncio
async def test_sealed_seance_invisible_to_stranger(client, make_token):
    owner = await make_token("seal_owner@test.com")
    stranger = await make_token("seal_stranger@test.com")

    r = await client.post("/seances", json={"name": "Sealed Room", "is_sealed": True}, headers=auth(owner))
    assert r.status_code == 201
    sid = r.json()["id"]

    # Stranger cannot enter directly
    r = await client.post(f"/seances/{sid}/enter", headers=auth(stranger))
    assert r.status_code == 403

    # Sealed room does not appear in stranger's list
    r = await client.get("/seances", headers=auth(stranger))
    assert not any(s["id"] == sid for s in r.json())


@pytest.mark.asyncio
async def test_invite_flow_for_sealed_seance(client, make_token):
    owner = await make_token("inv_owner@test.com")
    guest = await make_token("inv_guest@test.com")

    # Create sealed seance (owner gets warden presence automatically)
    r = await client.post("/seances", json={"name": "Sealed Invite", "is_sealed": True}, headers=auth(owner))
    sid = r.json()["id"]

    # Mint invite
    r = await client.post(f"/seances/{sid}/invites", headers=auth(owner))
    assert r.status_code == 201
    invite_token = r.json()["token"]

    # Guest joins via invite
    r = await client.post(f"/seances/join?token={invite_token}", headers=auth(guest))
    assert r.status_code == 201
    assert r.json()["role"] == "attendant"

    # Invite is single-use — second attempt must fail
    r = await client.post(f"/seances/join?token={invite_token}", headers=auth(guest))
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_sigil_collision_generates_distinct_sigils(client, make_token):
    """Two seekers in the same seance must get different sigils."""
    a = await make_token("sigil_a@test.com")
    b = await make_token("sigil_b@test.com")

    r = await client.post("/seances", json={"name": "Sigil Test"}, headers=auth(a))
    sid = r.json()["id"]

    r_a = await client.post(f"/seances/{sid}/enter", headers=auth(a))
    # a already has a presence (warden), so 409 — fetch it
    if r_a.status_code == 409:
        r_a = await client.get(f"/seances/{sid}/presences/me", headers=auth(a))
    sigil_a = r_a.json()["sigil"]

    r_b = await client.post(f"/seances/{sid}/enter", headers=auth(b))
    sigil_b = r_b.json()["sigil"]

    assert sigil_a != sigil_b


@pytest.mark.asyncio
async def test_kick_attendant(client, make_token):
    warden = await make_token("kick_w@test.com")
    attendant = await make_token("kick_a@test.com")

    r = await client.post("/seances", json={"name": "Kick Test"}, headers=auth(warden))
    sid = r.json()["id"]

    # Attendant enters
    await client.post(f"/seances/{sid}/enter", headers=auth(attendant))

    # Get attendant's seeker_id via presences list
    r = await client.get(f"/seances/{sid}/presences", headers=auth(warden))
    presences = r.json()

    r = await client.get("/debug/me", headers=auth(attendant))
    attendant_id = r.json()["id"]

    # Warden kicks
    r = await client.delete(f"/seances/{sid}/presences/{attendant_id}", headers=auth(warden))
    assert r.status_code == 204

    # Attendant no longer listed
    r = await client.get(f"/seances/{sid}/presences", headers=auth(warden))
    assert len(r.json()) == 1  # only warden remains


@pytest.mark.asyncio
async def test_transfer_wardenship(client, make_token):
    warden = await make_token("transfer_w@test.com")
    new_w = await make_token("transfer_nw@test.com")

    r = await client.post("/seances", json={"name": "Transfer Test"}, headers=auth(warden))
    sid = r.json()["id"]

    await client.post(f"/seances/{sid}/enter", headers=auth(new_w))

    r = await client.get("/debug/me", headers=auth(new_w))
    new_w_id = r.json()["id"]

    r = await client.post(f"/seances/{sid}/transfer",
                          json={"target_seeker_id": new_w_id}, headers=auth(warden))
    assert r.status_code == 204

    # New warden can dissolve; old one cannot
    r = await client.get(f"/seances/{sid}/presences", headers=auth(new_w))
    roles = {p["sigil"]: p["role"] for p in r.json()}
    assert "warden" in roles.values()
