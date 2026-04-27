"""Auth tests — register, login, bad credentials, socket token."""
import pytest


@pytest.mark.asyncio
async def test_register_and_login(client):
    r = await client.post("/auth/register", json={"email": "a@test.com", "password": "12345678"})
    assert r.status_code == 201

    r = await client.post("/auth/login", json={"email": "a@test.com", "password": "12345678"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_bad_password(client):
    await client.post("/auth/register", json={"email": "b@test.com", "password": "12345678"})
    r = await client.post("/auth/login", json={"email": "b@test.com", "password": "wrongpassword"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"email": "dup@test.com", "password": "12345678"}
    await client.post("/auth/register", json=payload)
    r = await client.post("/auth/register", json=payload)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_socket_token_requires_auth(client):
    r = await client.post("/auth/socket-token")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_socket_token_issued(client, make_token):
    token = await make_token("st@test.com")
    r = await client.post("/auth/socket-token", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert "socket_token" in r.json()
