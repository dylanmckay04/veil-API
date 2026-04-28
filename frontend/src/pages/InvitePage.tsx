import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { joinViaInvite } from '../api/seances'
import { useAuth } from '../store/auth'

export default function InvitePage() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const inviteToken = params.get('token')
    if (!inviteToken) {
      setError('No invitation token found.')
      return
    }

    if (!token) {
      sessionStorage.setItem('pendingInviteToken', inviteToken)
      navigate('/login', { replace: true })
      return
    }

    let cancelled = false
    const join = async () => {
      try {
        const presence = await joinViaInvite(inviteToken, token)
        if (!cancelled) navigate(`/seances/${presence.seance_id}`, { replace: true })
      } catch (err) {
        if (cancelled) return
        setError(err instanceof ApiError ? err.message : 'The invitation could not be accepted.')
      }
    }

    void join()
    return () => { cancelled = true }
  }, [token, params, navigate])

  if (error) {
    return (
      <div className="center-page">
        <p className="error-msg">{error}</p>
        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/lobby')}>
          Return to lobby
        </button>
      </div>
    )
  }

  return (
    <div className="center-page">
      <div className="spinner" />
      <span>Accepting your invitation…</span>
    </div>
  )
}
