import { get, post } from './client.js'
import type { GitHubLoginURLResponse, GoogleLoginURLResponse, LoginRequest, OperatorCreate, OperatorResponse, SocketTokenResponse, TokenResponse } from './types.js'

export const register = (body: OperatorCreate) =>
  post<OperatorResponse>('/auth/register', body)

export const login = (body: LoginRequest) =>
  post<TokenResponse>('/auth/login', body)

/** Mint a one-shot socket token. Must be consumed immediately — 60 s TTL. */
export const getSocketToken = (token: string) =>
  post<SocketTokenResponse>('/auth/socket-token', undefined, token)

export const getGithubLoginUrl = () =>
  get<GitHubLoginURLResponse>('/auth/github')

export const githubCallback = (body: { code: string; state: string }) =>
  post<TokenResponse>('/auth/github/callback', body)

export const getGoogleLoginUrl = () =>
  get<GoogleLoginURLResponse>('/auth/google')

export const googleCallback = (body: { code: string; state: string }) =>
  post<TokenResponse>('/auth/google/callback', body)
