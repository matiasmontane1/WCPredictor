import { useTodayMatches } from '../../api/client'
import { MatchCard } from '../../components/MatchCard'
import { SyncButton } from '../../components/SyncButton'

export function Dashboard() {
  const { data: matches, isLoading, error } = useTodayMatches()

  return (
    <div className="max-w-lg mx-auto px-4 pt-6 pb-24">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-white text-xl font-bold">Partidos de Hoy</h1>
        <SyncButton />
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
          Error al cargar los partidos. Verificá que el servidor esté corriendo.
        </div>
      )}

      {!isLoading && !error && matches?.length === 0 && (
        <div className="text-center py-16 text-slate-500">
          <div className="text-4xl mb-3">⚽</div>
          <p className="font-medium">No hay partidos hoy</p>
          <p className="text-sm mt-1">Sincronizá para actualizar</p>
        </div>
      )}

      {!isLoading && !error && matches && matches.length > 0 && (
        <div className="space-y-3">
          {matches.map((match) => (
            <MatchCard key={match.id} match={match} />
          ))}
        </div>
      )}
    </div>
  )
}
