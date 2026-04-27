// ── Auth ──────────────────────────────────────────────────────────────────────
export interface SeekerCreate  { email: string; password: string }
export interface SeekerResponse { id: number; email: string; created_at: string }
export interface LoginRequest  { email: string; password: string }
export interface TokenResponse { access_token: string; token_type: string }
export interface SocketTokenResponse { socket_token: string; jti: string }

// ── Seances ───────────────────────────────────────────────────────────────────
export interface SeanceCreate {
  name: string
  description?: string
  is_sealed?: boolean
}
export interface SeanceResponse {
  id: number
  name: string
  description: string | null
  is_sealed: boolean
  created_at: string
}
export interface SeanceDetail extends SeanceResponse {
  presence_count: number
}

// ── Presences ─────────────────────────────────────────────────────────────────
export type PresenceRole = 'warden' | 'attendant'
export interface PresenceResponse {
  sigil: string
  role: PresenceRole
  entered_at: string
}
export interface OwnPresenceResponse extends PresenceResponse {
  seance_id: number
}

// ── Whispers ──────────────────────────────────────────────────────────────────
export interface WhisperResponse {
  id: number
  seance_id: number
  sigil: string
  content: string
  created_at: string
}
export interface WhisperPage {
  items: WhisperResponse[]
  next_before_id: number | null
}

// ── WebSocket frames ──────────────────────────────────────────────────────────
export type WsMessage =
  | { op: 'whisper'; id: number; seance_id: number; sigil: string; content: string; created_at: string }
  | { op: 'enter';   sigil: string }
  | { op: 'depart';  sigil: string }
  | { op: 'dissolve' }
  | { op: 'error';   detail: string }
