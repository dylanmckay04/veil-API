import { useCallback, useEffect, useRef, useState } from 'react'
import { BASE_URL } from '../api/client'
import type { WsMessage } from '../api/types'

export type WsStatus = 'connecting' | 'connected' | 'reconnecting' | 'dead'

interface Options {
  seanceId: number
  token: string
  enabled: boolean
  /** Called for every inbound frame. */
  onMessage: (msg: WsMessage) => void
  /**
   * Called on every reconnect (not the initial connect) with the id of the
   * last whisper received before the drop, so the caller can backfill.
   */
  onReconnect: (lastSeenId: number) => void
}

export function useSeanceSocket({
  seanceId,
  token,
  enabled,
  onMessage,
  onReconnect,
}: Options) {
  const [wsStatus, setWsStatus] = useState<WsStatus>('connecting')

  // Always-current callback refs — avoids stale closures inside the effect
  const onMessageRef   = useRef(onMessage)
  const onReconnectRef = useRef(onReconnect)
  onMessageRef.current   = onMessage
  onReconnectRef.current = onReconnect

  // Shared mutable state that lives for the lifetime of the effect
  const lastSeenIdRef    = useRef<number | null>(null)
  const everConnectedRef = useRef(false)
  const wsRef            = useRef<WebSocket | null>(null)

  /**
   * Notify the hook of the highest whisper id currently loaded from REST so
   * that a future reconnect can compute the correct backfill window.
   */
  const setLastSeen = useCallback((id: number) => {
    lastSeenIdRef.current = Math.max(lastSeenIdRef.current ?? 0, id)
  }, [])

  /** Send a whisper frame. No-ops if the socket is not open. */
  const sendWhisper = useCallback((content: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ op: 'whisper', content }))
    }
  }, [])

  useEffect(() => {
    if (!enabled || !token) return

    let destroyed  = false
    let retryCount = 0

    const connect = async () => {
      if (destroyed) return
      setWsStatus('connecting')

      try {
        // Each WS connection requires a fresh one-shot token (60 s, single-use).
        const res = await fetch(`${BASE_URL}/auth/socket-token`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        })
        if (!res.ok || destroyed) { setWsStatus('dead'); return }
        const { socket_token } = (await res.json()) as { socket_token: string }
        if (destroyed) return

        const wsUrl =
          `${BASE_URL.replace(/^http/, 'ws')}/ws/seances/${seanceId}` +
          `?token=${encodeURIComponent(socket_token)}`
        const ws = new WebSocket(wsUrl)
        wsRef.current = ws

        ws.onopen = () => {
          if (destroyed) { ws.close(); return }
          const isReconnect = everConnectedRef.current
          everConnectedRef.current = true
          retryCount = 0
          setWsStatus('connected')
          // On a reconnect, ask the parent to backfill any missed whispers.
          if (isReconnect && lastSeenIdRef.current !== null) {
            onReconnectRef.current(lastSeenIdRef.current)
          }
        }

        ws.onmessage = ({ data }: MessageEvent<string>) => {
          try {
            const msg = JSON.parse(data) as WsMessage
            // Track highest seen whisper id so reconnects know where to backfill from.
            if (msg.op === 'whisper') {
              lastSeenIdRef.current = Math.max(lastSeenIdRef.current ?? 0, msg.id)
            }
            onMessageRef.current(msg)
          } catch { /* drop malformed frames */ }
        }

        ws.onerror = () => ws.close()

        ws.onclose = ({ code }: CloseEvent) => {
          if (destroyed) return
          // Auth/presence failures — surface immediately, don't retry.
          if (code === 4001 || code === 4003) { setWsStatus('dead'); return }
          if (retryCount >= 8)               { setWsStatus('dead'); return }
          const delay = Math.min(500 * 2 ** retryCount, 30_000)
          retryCount++
          setWsStatus('reconnecting')
          setTimeout(connect, delay)
        }
      } catch {
        if (!destroyed) {
          const delay = Math.min(500 * 2 ** retryCount, 30_000)
          retryCount++
          setWsStatus('reconnecting')
          setTimeout(connect, delay)
        }
      }
    }

    void connect()

    return () => {
      destroyed = true
      wsRef.current?.close(1000, 'unmounted')
      wsRef.current = null
    }
  }, [seanceId, token, enabled]) // reconnect only when these identity-level props change

  return { wsStatus, sendWhisper, setLastSeen }
}
