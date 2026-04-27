import { type FormEvent, useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { createSeance, listSeances } from '../api/seances'
import type { SeanceResponse } from '../api/types'
import { useAuth } from '../store/auth'

export default function LobbyPage() {
  const { token, clearToken } = useAuth()
  const navigate = useNavigate()

  const [seances,  setSeances]  = useState<SeanceResponse[]>([])
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState<string | null>(null)

  // Create form state
  const [name,        setName]        = useState('')
  const [description, setDescription] = useState('')
  const [isSealed,    setIsSealed]    = useState(false)
  const [creating,    setCreating]    = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  const fetchSeances = useCallback(async () => {
    if (!token) return
    try {
      setError(null)
      const data = await listSeances(token)
      setSeances(data)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) { clearToken(); return }
      setError('Could not load séances')
    } finally {
      setLoading(false)
    }
  }, [token, clearToken])

  useEffect(() => { void fetchSeances() }, [fetchSeances])

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault()
    if (!token || !name.trim()) return
    setCreateError(null)
    setCreating(true)
    try {
      const s = await createSeance(
        { name: name.trim(), description: description.trim() || undefined, is_sealed: isSealed },
        token,
      )
      setName(''); setDescription(''); setIsSealed(false)
      setSeances(prev => [...prev, s])
      navigate(`/seances/${s.id}`)
    } catch (err) {
      setCreateError(err instanceof ApiError ? err.message : 'Failed to create séance')
    } finally {
      setCreating(false)
    }
  }

  const enterSeance = (s: SeanceResponse) => {
    if (s.is_sealed) return
    navigate(`/seances/${s.id}`)
  }

  return (
    <div className="lobby-layout">
      <header className="lobby-header">
        <h1>Veil</h1>
        <div style={{ display: 'flex', gap: 10 }}>
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => void fetchSeances()}
          >
            Refresh
          </button>
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => { clearToken(); navigate('/login') }}
          >
            Sign out
          </button>
        </div>
      </header>

      <div className="lobby-body">
        {/* Create form */}
        <form className="create-form" onSubmit={handleCreate}>
          <h2>Open a new séance</h2>
          <div className="create-form-row">
            <input
              className="input"
              placeholder="Name"
              value={name}
              onChange={e => setName(e.target.value)}
              maxLength={100}
              required
              autoFocus
            />
            <input
              className="input"
              placeholder="Description (optional)"
              value={description}
              onChange={e => setDescription(e.target.value)}
              maxLength={300}
            />
          </div>
          <div className="create-form-footer">
            <label>
              <input
                type="checkbox"
                checked={isSealed}
                onChange={e => setIsSealed(e.target.checked)}
              />
              Sealed (invite-only)
            </label>
            <button
              className="btn btn-primary btn-sm"
              type="submit"
              disabled={creating || !name.trim()}
            >
              {creating ? 'Opening…' : 'Open séance'}
            </button>
            {createError && <span className="error-msg">{createError}</span>}
          </div>
        </form>

        {/* Séance list */}
        <div>
          <h2 style={{ fontSize: 15, color: 'var(--muted)', marginBottom: 14 }}>
            Active séances
          </h2>

          {loading ? (
            <div className="center-page" style={{ padding: '40px 0' }}>
              <div className="spinner" />
            </div>
          ) : error ? (
            <p className="error-msg">{error}</p>
          ) : seances.length === 0 ? (
            <p className="empty-state">No séances yet — open one above.</p>
          ) : (
            <div className="seance-grid">
              {seances.map(s => (
                <div
                  key={s.id}
                  className={`seance-card${s.is_sealed ? ' sealed' : ''}`}
                  onClick={() => enterSeance(s)}
                  role="button"
                  tabIndex={s.is_sealed ? -1 : 0}
                  onKeyDown={e => e.key === 'Enter' && enterSeance(s)}
                  title={s.is_sealed ? 'This séance is sealed' : undefined}
                >
                  <div className="seance-card-name">
                    {s.name}
                    {s.is_sealed && <span className="badge badge-sealed">Sealed</span>}
                  </div>
                  {s.description && (
                    <div className="seance-card-desc">{s.description}</div>
                  )}
                  <div className="seance-card-footer">
                    <span className="badge badge-open">
                      {new Date(s.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
