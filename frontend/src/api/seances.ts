import { del, get, post } from './client.js'
import type {
  OwnPresenceResponse,
  PresenceResponse,
  SeanceCreate,
  SeanceDetail,
  SeanceResponse,
  WhisperPage,
} from './types.js'

export const listSeances = (token: string) =>
  get<SeanceResponse[]>('/seances', token)

export const createSeance = (body: SeanceCreate, token: string) =>
  post<SeanceResponse>('/seances', body, token)

export const getSeance = (id: number, token: string) =>
  get<SeanceDetail>(`/seances/${id}`, token)

/** Enter a seance and receive a fresh sigil. 409 = already present. */
export const enterSeance = (id: number, token: string) =>
  post<OwnPresenceResponse>(`/seances/${id}/enter`, undefined, token)

/** Recover own presence after a page refresh (avoids re-entering). */
export const getMyPresence = (id: number, token: string) =>
  get<OwnPresenceResponse>(`/seances/${id}/presences/me`, token)

export const departSeance = (id: number, token: string) =>
  del<void>(`/seances/${id}/depart`, token)

export const dissolveSeance = (id: number, token: string) =>
  del<void>(`/seances/${id}`, token)

export const listPresences = (id: number, token: string) =>
  get<PresenceResponse[]>(`/seances/${id}/presences`, token)

export const getWhispers = (
  id: number,
  params: { limit?: number; before_id?: number },
  token: string,
) => {
  const q = new URLSearchParams()
  if (params.limit    !== undefined) q.set('limit',     String(params.limit))
  if (params.before_id !== undefined) q.set('before_id', String(params.before_id))
  const qs = q.toString()
  return get<WhisperPage>(`/seances/${id}/whispers${qs ? `?${qs}` : ''}`, token)
}
