import { useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTodayMatches } from '../../api/client'
import { MatchCard } from '../../components/MatchCard'
import { NextSyncWidget } from '../../components/NextSyncWidget'

export function Dashboard() {
  const { data: matches, isLoading, error } = useTodayMatches()
  const navigate = useNavigate()
  const tapCount = useRef(0)
  const tapTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  function handleTitleTap() {
    tapCount.current += 1
    if (tapTimer.current) clearTimeout(tapTimer.current)
    if (tapCount.current >= 5) {
      tapCount.current = 0
      navigate('/admin')
      return
    }
    tapTimer.current = setTimeout(() => { tapCount.current = 0 }, 1500)
  }

  return (
    <div className="max-w-lg mx-auto px-4 pt-6 pb-24">
      <div className="mb-2">
        <h1 className="text-white text-xl font-bold cursor-default select-none" onClick={handleTitleTap}>Partidos de Hoy</h1>
      </div>
      <div className="mb-6">
        <NextSyncWidget />
      </div>

      {isLoading && (
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <div key={i} className="bg-slate-800 rounded-xl h-36 animate-pulse" />
          ))}
        </div>
      )}

      {error && (
        <div className="bg-red-900/40 border border-red-700 rounded-xl p-4 text-red-300 text-sm text-center">
          Error al cargar los partidos. Verifica que el servidor esté corriendo.
        </div>
      )}

      {!isLoading && !error && matches?.length === 0 && (
        <div className="text-center py-16 text-slate-500">
          <div className="text-4xl mb-3">⚽</div>
          <p className="font-medium">No hay más partidos hoy</p>
        </div>
      )}

      {!isLoading && !error && matches && matches.length > 0 && (
        <div className="space-y-3">
          {matches
            .filter((m) => !['finished', 'awarded'].includes(m.status.toLowerCase()))
            .map((match) => (
              <MatchCard key={match.id} match={match} />
            ))}
        </div>
      )}
    </div>
  )
}
