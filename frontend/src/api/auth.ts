import { post } from './client'
import type { LoginRequest, SeekerCreate, SeekerResponse, SocketTokenResponse, TokenResponse } from './types'

export const register = (body: SeekerCreate) =>
  post<SeekerResponse>('/auth/register', body)

export const login = (body: LoginRequest) =>
  post<TokenResponse>('/auth/login', body)

/** Mint a one-shot socket token. Must be consumed immediately — 60 s TTL. */
export const getSocketToken = (token: string) =>
  post<SocketTokenResponse>('/auth/socket-token', undefined, token)
